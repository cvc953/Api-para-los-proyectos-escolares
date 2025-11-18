from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import mimetypes
import re
import os
import shutil
from pathlib import Path
import sys
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import List, Optional

from app.database import init_db, get_session
from app.models.models import (
    Estudiante, Profesor, Proyecto, ProyectoVersion, Calificacion
)
from app.schemas.schemas import (
    ProyectoCreate, ProyectoResponse, CalificarDTO, CalificacionResponse, DesempenoReporte
)
from app.auth import (
    create_access_token, decode_access_token, get_password_hash, verify_password
)
from app.crud import crud
from app.models.models import Curso, CursoEstudiante, Tarea
from app.schemas.schemas import CursoCreate, CursoResponse, AddStudentDTO, TareaCreate, TareaResponse

# Inicializar FastAPI
app = FastAPI(
    title="API Gestión Proyectos Escolares",
    description="API REST para gestión de proyectos escolares con versioning y calificaciones",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar BD
@app.on_event("startup")
def on_startup():
    init_db()

# Carpeta donde se guardan los archivos subidos.
# Intentamos crearla en orden: variable env -> /tmp/uploads. Si ninguna es escribible,
# deshabilitamos temporalmente el soporte de uploads para evitar que la app falle al importar.
UPLOAD_DIR = None
_preferred = os.environ.get("UPLOAD_DIR") or "./uploads"
try:
    p = Path(_preferred)
    p.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR = p
except Exception:
    try:
        p = Path("/tmp/uploads")
        p.mkdir(parents=True, exist_ok=True)
        UPLOAD_DIR = p
    except Exception:
        UPLOAD_DIR = None
        print("WARNING: uploads disabled — cannot create upload directory.", file=sys.stderr)

# ==================== RUTAS RAÍZ ====================
@app.get("/")
def root():
    return {
        "mensaje": "API de Gestión de Proyectos Escolares",
        "version": "1.0.0",
        "documentacion": "/docs",
        "endpoints": {
            "autenticacion": "/auth/login",
            "proyectos": "/proyectos",
            "calificaciones": "/calificaciones",
            "reportes": "/reportes"
        }
    }

# ==================== AUTENTICACIÓN ====================
@app.post("/auth/registro")
async def registro(
    request: Request,
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    nombre: Optional[str] = Form(None),
    apellido: Optional[str] = Form(None),
    rol: str = Form("estudiante"),
    session: Session = Depends(get_session)
):
    """Registrar nuevo usuario (estudiante, profesor o padre).

    Esta implementación acepta form-data (POST -F ...) y, como fallback,
    acepta parámetros por query (ej: ?email=...&password=...). Esto evita
    que una llamada con query provoque un 500 por falta de datos.
    """
    # Si los campos no vinieron como form, leer de query params
    if not email:
        email = request.query_params.get("email")
    if not password:
        password = request.query_params.get("password")
    if not nombre:
        nombre = request.query_params.get("nombre")
    if not apellido:
        apellido = request.query_params.get("apellido")
    if not rol:
        rol = request.query_params.get("rol", "estudiante")

    # Validaciones mínimas
    if not email or not password or not nombre or not apellido:
        raise HTTPException(status_code=422, detail="Faltan campos obligatorios: email, password, nombre, apellido")

    # Verificar si existe
    statement = select(Estudiante).where(Estudiante.email == email)
    if session.exec(statement).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    if rol == "estudiante":
        usuario = Estudiante(nombre=nombre, apellido=apellido, email=email, password_hash=get_password_hash(password))
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        return {"id": usuario.id, "email": usuario.email, "rol": "estudiante"}
    else:
        usuario = Profesor(nombre=nombre, apellido=apellido, email=email, password_hash=get_password_hash(password))
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        return {"id": usuario.id, "email": usuario.email, "rol": "profesor"}

@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    """Login y obtener token JWT"""
    # Validar que el campo 'email' tenga formato de correo
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=422, detail="El campo 'email' debe ser una dirección de correo válida")
    # Intentamos localizar al usuario en la tabla Estudiante
    statement = select(Estudiante).where(Estudiante.email == email)
    user = session.exec(statement).first()
    role = None

    # Si es estudiante y la contraseña coincide, definimos role
    if user and verify_password(password, user.password_hash or ""):
        role = "estudiante"
    else:
        # Si no, buscamos en tabla Profesor
        statement = select(Profesor).where(Profesor.email == email)
        user = session.exec(statement).first()
        if user and verify_password(password, user.password_hash or ""):
            role = "profesor"

    if not user or not role:
        # No se encontró usuario válido
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Incluir role en el payload del token para que clientes/servicios lo conozcan
    token = create_access_token(data={"sub": user.email, "id": user.id, "role": role})
    # Devolver también nombre y correo para que el cliente conozca la identidad básica
    nombre = getattr(user, "nombre", None)
    apellido = getattr(user, "apellido", None)
    email_resp = getattr(user, "email", None)
    nombre_completo = f"{nombre} {apellido}".strip() if nombre or apellido else None
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario_id": user.id,
        "rol": role,
        "nombre": nombre,
        "apellido": apellido,
        "email": email_resp,
        "nombre_completo": nombre_completo
    }

# ==================== PROYECTOS ====================
@app.post("/proyectos", response_model=ProyectoResponse)
def crear_proyecto(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    estudiante_id: Optional[int] = Form(None),
    curso_id: Optional[int] = Form(None),
    profesor_id: int = Form(...),
    fecha_entrega: Optional[str] = Form(None),
    comentarios_version: Optional[str] = Form(None),
    file: UploadFile = File(None),
    session: Session = Depends(get_session)
):
    """Crear nuevo proyecto y opcionalmente subir el archivo inicial.

    Se acepta multipart/form-data con los campos como `-F` en curl y un archivo
    en el campo `file`.
    """
    # Validar profesor
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=400, detail="Profesor no encontrado")

    # Validar asignación: preferimos curso_id si fue provisto; si no, usar estudiante_id
    estudiante = None
    curso = None
    if curso_id is not None:
        curso = session.get(Curso, curso_id)
        if not curso:
            raise HTTPException(status_code=400, detail="Curso no encontrado")
    else:
        # Si no hay curso, validar estudiante (legacy)
        if estudiante_id is None:
            raise HTTPException(status_code=422, detail="Debe indicar 'curso_id' o 'estudiante_id' al crear un proyecto")
        estudiante = session.get(Estudiante, estudiante_id)
        if not estudiante:
            raise HTTPException(status_code=400, detail="Estudiante no encontrado")
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=400, detail="Profesor no encontrado")

    # Parse fecha_entrega si viene como string
    fecha_dt = None
    if fecha_entrega:
        try:
            fecha_dt = datetime.fromisoformat(fecha_entrega)
        except Exception:
            raise HTTPException(status_code=422, detail="fecha_entrega debe ser ISO datetime (ej. 2025-12-01T23:59:00)")

    nuevo_proyecto = Proyecto(
        titulo=titulo,
        descripcion=descripcion,
        estudiante_id=estudiante_id if estudiante is not None else None,
        curso_id=curso_id if curso is not None else None,
        profesor_id=profesor_id,
        fecha_entrega=fecha_dt,
        version_actual=1,
        calificacion_actual=None
    )

    try:
        session.add(nuevo_proyecto)
        session.commit()
        session.refresh(nuevo_proyecto)

        archivo_path = None
        # Guardar archivo si se subió
        if file is not None:
            if UPLOAD_DIR is None:
                raise HTTPException(status_code=503, detail="Subida de archivos deshabilitada en este servidor")
            safe_name = f"{nuevo_proyecto.id}_" + Path(file.filename).name
            dest = UPLOAD_DIR / safe_name
            with dest.open("wb") as out_f:
                shutil.copyfileobj(file.file, out_f)
            archivo_path = str(dest)

        # Crear primera versión
        primera_version = ProyectoVersion(
            proyecto_id=nuevo_proyecto.id,
            numero_version=1,
            archivo_path=archivo_path,
            descripcion=comentarios_version,
            es_version_actual=True
        )
        session.add(primera_version)
        session.commit()

        return ProyectoResponse(
            id=nuevo_proyecto.id,
            titulo=nuevo_proyecto.titulo,
            descripcion=nuevo_proyecto.descripcion,
            estudiante_id=nuevo_proyecto.estudiante_id,
            curso_id=nuevo_proyecto.curso_id,
            profesor_id=nuevo_proyecto.profesor_id,
            fecha_entrega=nuevo_proyecto.fecha_entrega,
            fecha_creacion=nuevo_proyecto.fecha_creacion,
            version_actual=1,
            calificacion_actual=None,
            total_versiones=1
        )
    except Exception as e:
        # Intentar rollback y devolver un error legible
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al crear proyecto: {str(e)}")


# ==================== ASIGNACIONES (Moodle-like) ====================
@app.post("/asignaciones", response_model=ProyectoResponse)
def crear_asignacion(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    curso_id: int = Form(...),
    profesor_id: int = Form(...),
    fecha_entrega: Optional[str] = Form(None),
    comentarios_version: Optional[str] = Form(None),
    file: UploadFile = File(None),
    session: Session = Depends(get_session)
):
    """Crear una asignación/tarea asociada a un curso (similar a Moodle)."""
    # Validar profesor y curso
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=400, detail="Profesor no encontrado")
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=400, detail="Curso no encontrado")

    # Parse fecha_entrega si viene como string
    fecha_dt = None
    if fecha_entrega:
        try:
            fecha_dt = datetime.fromisoformat(fecha_entrega)
        except Exception:
            raise HTTPException(status_code=422, detail="fecha_entrega debe ser ISO datetime (ej. 2025-12-01T23:59:00)")

    nuevo_proyecto = Proyecto(
        titulo=titulo,
        descripcion=descripcion,
        estudiante_id=None,
        curso_id=curso_id,
        profesor_id=profesor_id,
        fecha_entrega=fecha_dt,
        version_actual=1,
        calificacion_actual=None
    )

    try:
        session.add(nuevo_proyecto)
        session.commit()
        session.refresh(nuevo_proyecto)

        archivo_path = None
        if file is not None:
            if UPLOAD_DIR is None:
                raise HTTPException(status_code=503, detail="Subida de archivos deshabilitada en este servidor")
            safe_name = f"{nuevo_proyecto.id}_" + Path(file.filename).name
            dest = UPLOAD_DIR / safe_name
            with dest.open("wb") as out_f:
                shutil.copyfileobj(file.file, out_f)
            archivo_path = str(dest)

        # Primera versión (sin estudiante, entrega inicial del profesor o recurso)
        primera_version = ProyectoVersion(
            proyecto_id=nuevo_proyecto.id,
            numero_version=1,
            archivo_path=archivo_path,
            descripcion=comentarios_version,
            es_version_actual=True
        )
        session.add(primera_version)
        session.commit()

        return ProyectoResponse(
            id=nuevo_proyecto.id,
            titulo=nuevo_proyecto.titulo,
            descripcion=nuevo_proyecto.descripcion,
            estudiante_id=nuevo_proyecto.estudiante_id,
            profesor_id=nuevo_proyecto.profesor_id,
            fecha_entrega=nuevo_proyecto.fecha_entrega,
            fecha_creacion=nuevo_proyecto.fecha_creacion,
            version_actual=1,
            calificacion_actual=None,
            total_versiones=1
        )
    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al crear asignación: {str(e)}")


@app.post("/asignaciones/{asignacion_id}/entregas")
def entregar_asignacion(
    asignacion_id: int,
    descripcion: str = Form(...),
    file: UploadFile = File(None),
    session: Session = Depends(get_session),
    request: Request = None
):
    """Endpoint para que un estudiante entregue una asignación (proyecto asignado a un curso)."""
    proyecto = session.get(Proyecto, asignacion_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    # Obtener estudiante autenticado desde token
    estudiante_autenticado_id = None
    try:
        auth_header = None
        if request is not None:
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                payload = decode_access_token(token)
                if payload and payload.get('role') == 'estudiante':
                    estudiante_autenticado_id = payload.get('id')
    except Exception:
        pass

    if estudiante_autenticado_id is None:
        raise HTTPException(status_code=401, detail="Debes autenticarte como estudiante para entregar esta asignación")

    # Verificar inscripción en el curso
    if proyecto.curso_id is None:
        raise HTTPException(status_code=400, detail="Esta asignación no está asociada a un curso")
    stmt_ins = select(CursoEstudiante).where(
        CursoEstudiante.curso_id == proyecto.curso_id,
        CursoEstudiante.estudiante_id == estudiante_autenticado_id
    )
    ins = session.exec(stmt_ins).first()
    if not ins:
        raise HTTPException(status_code=403, detail="No estás inscrito en el curso asignado")

    # Obtener versiones y calcular número de versión para este estudiante
    versiones = crud.obtener_versiones(session, asignacion_id)
    versiones_estudiante = [v for v in versiones if getattr(v, 'estudiante_id', None) == estudiante_autenticado_id]
    for v in versiones_estudiante:
        v.es_version_actual = False
    numero_version_estudiante = len(versiones_estudiante) + 1

    archivo_path = None
    if file is not None:
        if UPLOAD_DIR is None:
            raise HTTPException(status_code=503, detail="Subida de archivos deshabilitada en este servidor")
        safe_name = f"{asignacion_id}_est{estudiante_autenticado_id}_v{numero_version_estudiante}_" + Path(file.filename).name
        dest = UPLOAD_DIR / safe_name
        with dest.open("wb") as out_f:
            shutil.copyfileobj(file.file, out_f)
        archivo_path = str(dest)

    nueva_version = ProyectoVersion(
        proyecto_id=asignacion_id,
        estudiante_id=estudiante_autenticado_id,
        numero_version=numero_version_estudiante,
        descripcion=descripcion,
        archivo_path=archivo_path,
        es_version_actual=True
    )
    proyecto.version_actual = nueva_version.numero_version
    session.add(nueva_version)
    session.add(proyecto)
    session.commit()
    session.refresh(nueva_version)

    return {"id": nueva_version.id, "numero_version": nueva_version.numero_version, "fecha": nueva_version.fecha_subida}


@app.get("/asignaciones/{asignacion_id}/entregas")
def obtener_entregas_asignacion(asignacion_id: int, session: Session = Depends(get_session)):
    """Obtener todas las entregas de una asignación, agrupadas por estudiante."""
    proyecto = session.get(Proyecto, asignacion_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    versiones = crud.obtener_versiones(session, asignacion_id)
    # Agrupar por estudiante
    versiones_por_estudiante = {}
    for v in versiones:
        est_id = getattr(v, 'estudiante_id', None)
        if est_id not in versiones_por_estudiante:
            versiones_por_estudiante[est_id] = []
        versiones_por_estudiante[est_id].append(v)

    entregas = []
    for est_id, vers in versiones_por_estudiante.items():
        estudiante_info = None
        if est_id is not None:
            estudiante = session.get(Estudiante, est_id)
            if estudiante:
                estudiante_info = {
                    "id": estudiante.id,
                    "nombre": estudiante.nombre,
                    "apellido": estudiante.apellido,
                    "email": estudiante.email,
                    "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}"
                }
        entregas.append({
            "estudiante": estudiante_info,
            "versiones": [
                {
                    "id": v.id,
                    "numero_version": v.numero_version,
                    "descripcion": v.descripcion,
                    "fecha_subida": v.fecha_subida,
                    "es_version_actual": v.es_version_actual,
                    "tiene_archivo": v.archivo_path is not None
                }
                for v in vers
            ]
        })

    return {"proyecto_id": proyecto.id, "titulo": proyecto.titulo, "entregas_por_estudiante": entregas}

@app.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(proyecto_id: int, session: Session = Depends(get_session), request: Request = None):
    """Obtener detalle de un proyecto"""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    versiones = crud.obtener_versiones(session, proyecto_id)

    # Determinar si el usuario autenticado (si hay token Bearer) es un estudiante
    # asignado a este proyecto. Devolver la bandera en la respuesta para que el
    # cliente pueda mostrar u ocultar controles (ej. subir versión).
    es_asignado = None
    try:
        auth_header = None
        if request is not None:
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                payload = decode_access_token(token)
                if payload and payload.get('role') == 'estudiante':
                    est_id = payload.get('id')
                    if est_id is not None:
                        # Caso 1: Proyecto asignado a curso - verificar inscripción
                        if proyecto.curso_id is not None:
                            stmt = select(CursoEstudiante).where(
                                CursoEstudiante.curso_id == proyecto.curso_id, 
                                CursoEstudiante.estudiante_id == est_id
                            )
                            enlace = session.exec(stmt).first()
                            es_asignado = enlace is not None
                        # Caso 2: Proyecto asignado directamente al estudiante
                        elif proyecto.estudiante_id is not None and proyecto.estudiante_id == est_id:
                            es_asignado = True
                        else:
                            es_asignado = False
    except Exception:
        es_asignado = None

    return ProyectoResponse(
        id=proyecto.id,
        titulo=proyecto.titulo,
        descripcion=proyecto.descripcion,
        estudiante_id=proyecto.estudiante_id,
        curso_id=proyecto.curso_id,
        profesor_id=proyecto.profesor_id,
        fecha_entrega=proyecto.fecha_entrega,
        fecha_creacion=proyecto.fecha_creacion,
        version_actual=proyecto.version_actual,
        calificacion_actual=proyecto.calificacion_actual,
        total_versiones=len(versiones),
        es_estudiante_asignado=es_asignado
    )


@app.get("/proyectos/{proyecto_id}/archivo")
def descargar_proyecto(proyecto_id: int, session: Session = Depends(get_session)):
    """Descargar el archivo de la versión actual de un proyecto."""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    versiones = crud.obtener_versiones(session, proyecto_id)
    if not versiones:
        raise HTTPException(status_code=404, detail="No hay versiones para este proyecto")

    current = next((v for v in versiones if v.es_version_actual), None)
    if not current or not current.archivo_path:
        raise HTTPException(status_code=404, detail="No hay archivo asociado a la versión actual")

    path = Path(current.archivo_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")

    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    # Intentamos recuperar el nombre original si el archivo fue guardado con prefijo
    name = path.name
    # patrones: "{id}_originalname" o "{id}_v{num}_originalname"
    m = re.match(r"^\d+_v\d+_(.+)$", name)
    if m:
        display_name = m.group(1)
    else:
        m2 = re.match(r"^(\d+)_(.+)$", name)
        display_name = m2.group(2) if m2 else name
    return FileResponse(path, filename=display_name, media_type=mime)


@app.get("/proyectos/{proyecto_id}/versiones/{version_id}/archivo")
def descargar_version_archivo(proyecto_id: int, version_id: int, session: Session = Depends(get_session)):
    """Descargar el archivo de una versión específica de un proyecto."""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    versiones = crud.obtener_versiones(session, proyecto_id)
    version = next((v for v in versiones if v.id == version_id), None)
    if not version or not version.archivo_path:
        raise HTTPException(status_code=404, detail="Versión o archivo no encontrado")

    path = Path(version.archivo_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")

    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    name = path.name
    m = re.match(r"^\d+_v\d+_(.+)$", name)
    if m:
        display_name = m.group(1)
    else:
        m2 = re.match(r"^(\d+)_(.+)$", name)
        display_name = m2.group(2) if m2 else name
    return FileResponse(path, filename=display_name, media_type=mime)

@app.get("/proyectos/estudiante/{estudiante_id}")
def obtener_proyectos_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    """Listar todos los proyectos de un estudiante"""
    # Proyectos directamente asignados al estudiante
    stmt_direct = select(Proyecto).where(Proyecto.estudiante_id == estudiante_id)
    proyectos_direct = session.exec(stmt_direct).all()

    # Proyectos asignados a cursos donde el estudiante está inscrito
    stmt_cursos = select(CursoEstudiante).where(CursoEstudiante.estudiante_id == estudiante_id)
    cursos_enlace = session.exec(stmt_cursos).all()
    curso_ids = [c.curso_id for c in cursos_enlace]
    proyectos_curso = []
    if curso_ids:
        stmt_c = select(Proyecto).where(Proyecto.curso_id.in_(curso_ids))
        proyectos_curso = session.exec(stmt_c).all()

    proyectos = proyectos_direct + [p for p in proyectos_curso if p not in proyectos_direct]
    if not proyectos:
        raise HTTPException(status_code=404, detail="No hay proyectos para este estudiante")
    return proyectos

@app.get("/proyectos/profesor/{profesor_id}")
def obtener_proyectos_profesor(profesor_id: int, session: Session = Depends(get_session)):
    """Listar todos los proyectos asignados a un profesor"""
    statement = select(Proyecto).where(Proyecto.profesor_id == profesor_id)
    proyectos = session.exec(statement).all()
    if not proyectos:
        raise HTTPException(status_code=404, detail="No hay proyectos para este profesor")
    return proyectos


# ==================== CURSOS ====================
@app.post("/cursos", response_model=CursoResponse)
def crear_curso(curso: CursoCreate, session: Session = Depends(get_session)):
    """Crear un curso por parte de un profesor."""
    profesor = session.get(Profesor, curso.profesor_id)
    if not profesor:
        raise HTTPException(status_code=400, detail="Profesor no encontrado")

    nuevo = Curso(
        nombre=curso.nombre,
        descripcion=curso.descripcion,
        profesor_id=curso.profesor_id
    )
    try:
        creado = crud.crear_curso(session, nuevo)
        return CursoResponse(
            id=creado.id,
            nombre=creado.nombre,
            descripcion=creado.descripcion,
            profesor_id=creado.profesor_id,
            fecha_creacion=creado.fecha_creacion
        )
    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al crear curso: {str(e)}")


@app.post("/cursos/{curso_id}/estudiantes")
def agregar_estudiante_curso(curso_id: int, dto: AddStudentDTO, session: Session = Depends(get_session)):
    """Agregar un estudiante a un curso existente.
    
    Al inscribir un estudiante en un curso, automáticamente tiene acceso a TODOS los 
    proyectos/asignaciones de ese curso (pasados, presentes y futuros).
    No se crean copias - el sistema valida la inscripción al curso al momento de subir entregas.
    """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    estudiante = session.get(Estudiante, dto.estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=400, detail="Estudiante no encontrado")

    # Verificar si ya está inscrito
    stmt_check = select(CursoEstudiante).where(
        CursoEstudiante.curso_id == curso_id,
        CursoEstudiante.estudiante_id == dto.estudiante_id
    )
    ya_inscrito = session.exec(stmt_check).first()
    if ya_inscrito:
        raise HTTPException(status_code=400, detail="El estudiante ya está inscrito en este curso")

    enlace = CursoEstudiante(curso_id=curso_id, estudiante_id=dto.estudiante_id)
    try:
        creado = crud.agregar_estudiante_a_curso(session, enlace)
        
        # Contar proyectos existentes en el curso
        stmt_proyectos = select(Proyecto).where(Proyecto.curso_id == curso_id)
        proyectos_curso = session.exec(stmt_proyectos).all()
        
        return {
            "id": creado.id, 
            "curso_id": creado.curso_id, 
            "estudiante_id": creado.estudiante_id,
            "proyectos_asignados": len(proyectos_curso),
            "mensaje": f"Estudiante inscrito correctamente. Tiene acceso a {len(proyectos_curso)} proyecto(s) del curso."
        }
    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al agregar estudiante al curso: {str(e)}")


@app.get("/cursos/{curso_id}/estudiantes")
def listar_estudiantes_curso(curso_id: int, session: Session = Depends(get_session)):
    """Listar estudiantes inscritos en un curso."""
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    # Obtener enlaces curso-estudiante
    stmt = select(CursoEstudiante).where(CursoEstudiante.curso_id == curso_id)
    enlaces = session.exec(stmt).all()

    estudiantes = []
    for e in enlaces:
        est = session.get(Estudiante, e.estudiante_id)
        if est:
            estudiantes.append({
                "estudiante_id": est.id,
                "nombre": est.nombre,
                "apellido": est.apellido,
                "email": est.email
            })

    return estudiantes


@app.get("/cursos/profesor/{profesor_id}")
def listar_cursos_profesor(profesor_id: int, session: Session = Depends(get_session)):
    """Listar cursos de un profesor"""
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    cursos = crud.obtener_cursos_por_profesor(session, profesor_id)
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "profesor_id": c.profesor_id,
            "fecha_creacion": c.fecha_creacion
        }
        for c in cursos
    ]


@app.post("/cursos/{curso_id}/tareas", response_model=TareaResponse)
def crear_tarea_curso(
    curso_id: int,
    titulo: str = Form(...),
    descripcion: Optional[str] = Form(None),
    fecha_entrega: Optional[str] = Form(None),
    file: UploadFile = File(None),
    session: Session = Depends(get_session)
):
    """Crear una tarea asociada a un curso. Acepta archivo opcional en `file`."""
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    fecha_dt = None
    if fecha_entrega:
        try:
            fecha_dt = datetime.fromisoformat(fecha_entrega)
        except Exception:
            raise HTTPException(status_code=422, detail="fecha_entrega debe ser ISO datetime")

    archivo_path = None
    if file is not None:
        if UPLOAD_DIR is None:
            raise HTTPException(status_code=503, detail="Subida de archivos deshabilitada en este servidor")
        safe_name = f"curso{curso_id}_tarea_{file.filename}"
        dest = UPLOAD_DIR / safe_name
        try:
            with dest.open("wb") as out_f:
                shutil.copyfileobj(file.file, out_f)
            archivo_path = str(dest)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")

    tarea = Tarea(
        curso_id=curso_id,
        titulo=titulo,
        descripcion=descripcion,
        fecha_entrega=fecha_dt,
        archivo_path=archivo_path
    )

    try:
        creado = crud.crear_tarea(session, tarea)
        return TareaResponse(
            id=creado.id,
            curso_id=creado.curso_id,
            titulo=creado.titulo,
            descripcion=creado.descripcion,
            fecha_entrega=creado.fecha_entrega,
            fecha_creacion=creado.fecha_creacion
        )
    except Exception as e:
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al crear tarea: {str(e)}")


@app.get("/cursos/{curso_id}/tareas")
def listar_tareas_curso(curso_id: int, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    tareas = crud.obtener_tareas_por_curso(session, curso_id)
    return [
        {
            "id": t.id,
            "curso_id": t.curso_id,
            "titulo": t.titulo,
            "descripcion": t.descripcion,
            "fecha_entrega": t.fecha_entrega,
            "fecha_creacion": t.fecha_creacion
        }
        for t in tareas
    ]


@app.get("/usuarios/{usuario_id}")
def obtener_perfil(usuario_id: int, session: Session = Depends(get_session)):
    """Obtener perfil de un usuario (estudiante o profesor). Devuelve rol, nombre y correo."""
    estudiante = session.get(Estudiante, usuario_id)
    if estudiante:
        return {
            "id": estudiante.id,
            "rol": "estudiante",
            "nombre": estudiante.nombre,
            "apellido": estudiante.apellido,
            "email": estudiante.email
        }
    profesor = session.get(Profesor, usuario_id)
    if profesor:
        return {
            "id": profesor.id,
            "rol": "profesor",
            "nombre": profesor.nombre,
            "apellido": profesor.apellido,
            "email": profesor.email
        }
    raise HTTPException(status_code=404, detail="Usuario no encontrado")


@app.get("/estudiantes")
def listar_estudiantes(session: Session = Depends(get_session)):
    """Listar todos los estudiantes registrados."""
    stmt = select(Estudiante)
    filas = session.exec(stmt).all()
    return [
        {"id": e.id, "nombre": e.nombre, "apellido": e.apellido, "email": e.email}
        for e in filas
    ]

# ==================== VERSIONES ====================
@app.post("/proyectos/{proyecto_id}/versiones")
def subir_version(
    proyecto_id: int,
    descripcion: str = Form(...),
    file: UploadFile = File(None),
    session: Session = Depends(get_session),
    request: Request = None
):
    """Subir nueva versión de un proyecto. Acepta un archivo opcional en el campo `file`."""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Si la petición incluye Authorization Bearer token, intentar decodificar
    # y si corresponde a un estudiante, validar que esté inscrito en el curso del proyecto.
    estudiante_autenticado_id = None
    try:
        auth_header = None
        if request is not None:
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                payload = decode_access_token(token)
                if payload and payload.get('role') == 'estudiante':
                    estudiante_autenticado_id = payload.get('id')
    except Exception:
        pass

    # Validar que el estudiante autenticado tenga permiso para subir versiones a este proyecto
    if estudiante_autenticado_id is not None:
        estudiante_tiene_permiso = False
        
        # Caso 1: Proyecto asignado directamente al estudiante
        if proyecto.estudiante_id == estudiante_autenticado_id:
            estudiante_tiene_permiso = True
        # Caso 2: Proyecto asignado a un curso y el estudiante está inscrito en ese curso
        elif proyecto.curso_id is not None:
            stmt_inscripcion = select(CursoEstudiante).where(
                CursoEstudiante.curso_id == proyecto.curso_id,
                CursoEstudiante.estudiante_id == estudiante_autenticado_id
            )
            inscripcion = session.exec(stmt_inscripcion).first()
            if inscripcion:
                estudiante_tiene_permiso = True
                # NO asignar proyecto.estudiante_id - los proyectos de curso son para todos los estudiantes
        
        if not estudiante_tiene_permiso:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para subir versiones a este proyecto. Debes estar inscrito en el curso asignado."
            )

    # Obtener versiones del estudiante autenticado (si aplica)
    # Cada estudiante tiene su propia secuencia de versiones independiente
    versiones = crud.obtener_versiones(session, proyecto_id)
    
    # Filtrar versiones del estudiante actual y marcar anteriores como no actuales
    if estudiante_autenticado_id is not None:
        versiones_estudiante = [v for v in versiones if getattr(v, 'estudiante_id', None) == estudiante_autenticado_id]
        for v in versiones_estudiante:
            v.es_version_actual = False
        numero_version_estudiante = len(versiones_estudiante) + 1
    else:
        # Si no hay estudiante autenticado (profesores u otros), usar lógica anterior
        for v in versiones:
            v.es_version_actual = False
        numero_version_estudiante = len(versiones) + 1

    archivo_path = None
    if file is not None:
        if UPLOAD_DIR is None:
            raise HTTPException(status_code=503, detail="Subida de archivos deshabilitada en este servidor")
        # Incluir estudiante_id en el nombre del archivo para evitar conflictos
        estudiante_suffix = f"_est{estudiante_autenticado_id}" if estudiante_autenticado_id else ""
        safe_name = f"{proyecto_id}{estudiante_suffix}_v{numero_version_estudiante}_" + Path(file.filename).name
        dest = UPLOAD_DIR / safe_name
        with dest.open("wb") as out_f:
            shutil.copyfileobj(file.file, out_f)
        archivo_path = str(dest)

    # Crear nueva versión con estudiante_id
    nueva_version = ProyectoVersion(
        proyecto_id=proyecto_id,
        estudiante_id=estudiante_autenticado_id,
        numero_version=numero_version_estudiante,
        descripcion=descripcion,
        archivo_path=archivo_path,
        es_version_actual=True
    )

    proyecto.version_actual = nueva_version.numero_version

    session.add(nueva_version)
    session.add(proyecto)
    session.commit()
    session.refresh(nueva_version)

    return {"id": nueva_version.id, "numero_version": nueva_version.numero_version, "fecha": nueva_version.fecha_subida}

@app.get("/proyectos/{proyecto_id}/versiones")
def obtener_versiones_proyecto(proyecto_id: int, session: Session = Depends(get_session), request: Request = None):
    """Obtener historial de versiones de un proyecto con información del estudiante.
    
    - Estudiantes: ven solo sus propias versiones
    - Profesores: ven todas las versiones agrupadas por estudiante
    """
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    versiones = crud.obtener_versiones(session, proyecto_id)
    if not versiones:
        raise HTTPException(status_code=404, detail="No hay versiones para este proyecto")
    
    # Detectar rol del usuario autenticado
    estudiante_autenticado_id = None
    es_profesor = False
    try:
        auth_header = None
        if request is not None:
            auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                payload = decode_access_token(token)
                if payload:
                    role = payload.get('role')
                    if role == 'estudiante':
                        estudiante_autenticado_id = payload.get('id')
                    elif role == 'profesor':
                        es_profesor = True
    except Exception:
        pass
    
    # Filtrar versiones según el rol
    if estudiante_autenticado_id is not None:
        # Estudiante: solo sus versiones
        versiones = [v for v in versiones if getattr(v, 'estudiante_id', None) == estudiante_autenticado_id]
        if not versiones:
            raise HTTPException(status_code=404, detail="No has subido versiones para este proyecto")
    
    # Agrupar versiones por estudiante para profesores
    if es_profesor or estudiante_autenticado_id is None:
        # Agrupar por estudiante
        versiones_por_estudiante = {}
        for v in versiones:
            est_id = getattr(v, 'estudiante_id', None)
            if est_id not in versiones_por_estudiante:
                versiones_por_estudiante[est_id] = []
            versiones_por_estudiante[est_id].append(v)
        
        entregas = []
        for est_id, vers in versiones_por_estudiante.items():
            estudiante_info = None
            if est_id:
                estudiante = session.get(Estudiante, est_id)
                if estudiante:
                    estudiante_info = {
                        "id": estudiante.id,
                        "nombre": estudiante.nombre,
                        "apellido": estudiante.apellido,
                        "email": estudiante.email,
                        "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}"
                    }
            
            entregas.append({
                "estudiante": estudiante_info,
                "versiones": [
                    {
                        "id": v.id,
                        "numero_version": v.numero_version,
                        "descripcion": v.descripcion,
                        "fecha_subida": v.fecha_subida,
                        "es_version_actual": v.es_version_actual,
                        "tiene_archivo": v.archivo_path is not None
                    }
                    for v in vers
                ]
            })
        
        return {
            "proyecto_id": proyecto.id,
            "titulo": proyecto.titulo,
            "entregas_por_estudiante": entregas
        }
    else:
        # Estudiante: vista simple de sus versiones
        estudiante_info = None
        if estudiante_autenticado_id:
            estudiante = session.get(Estudiante, estudiante_autenticado_id)
            if estudiante:
                estudiante_info = {
                    "id": estudiante.id,
                    "nombre": estudiante.nombre,
                    "apellido": estudiante.apellido,
                    "email": estudiante.email
                }
        
        return {
            "proyecto_id": proyecto.id,
            "titulo": proyecto.titulo,
            "estudiante": estudiante_info,
            "versiones": [
                {
                    "id": v.id,
                    "numero_version": v.numero_version,
                    "descripcion": v.descripcion,
                    "fecha_subida": v.fecha_subida,
                    "es_version_actual": v.es_version_actual,
                    "tiene_archivo": v.archivo_path is not None
                }
                for v in versiones
            ]
        }

@app.get("/cursos/{curso_id}/entregas")
def obtener_entregas_curso(curso_id: int, session: Session = Depends(get_session)):
    """Obtener todas las entregas (versiones) de todos los estudiantes de un curso.
    
    Útil para que el profesor revise y califique las entregas de manera organizada.
    Devuelve proyectos agrupados por estudiante con sus respectivas versiones.
    """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Obtener proyectos asignados al curso
    stmt_proyectos = select(Proyecto).where(Proyecto.curso_id == curso_id)
    proyectos = session.exec(stmt_proyectos).all()
    
    # Obtener estudiantes inscritos en el curso
    stmt_estudiantes = select(CursoEstudiante).where(CursoEstudiante.curso_id == curso_id)
    inscripciones = session.exec(stmt_estudiantes).all()
    estudiante_ids = [i.estudiante_id for i in inscripciones]
    
    # Construir respuesta organizada por proyecto y por estudiante
    resultado = []
    for proyecto in proyectos:
        versiones_todas = crud.obtener_versiones(session, proyecto.id)
        
        # Agrupar versiones por estudiante
        entregas_por_estudiante = []
        for est_id in estudiante_ids:
            estudiante = session.get(Estudiante, est_id)
            if not estudiante:
                continue
            
            # Filtrar versiones de este estudiante
            versiones_estudiante = [v for v in versiones_todas if getattr(v, 'estudiante_id', None) == est_id]
            
            # Obtener calificación del estudiante para este proyecto (si existe)
            # Nota: actualmente Calificacion no tiene estudiante_id, así que mostramos la calificación general del proyecto
            stmt_cal = select(Calificacion).where(Calificacion.proyecto_id == proyecto.id).order_by(Calificacion.fecha_calificacion.desc())
            calificaciones = session.exec(stmt_cal).all()
            calificacion_actual = None
            if calificaciones:
                cal = calificaciones[0]
                calificacion_actual = {
                    "puntaje": cal.puntaje,
                    "comentarios": cal.comentarios,
                    "fecha": cal.fecha_calificacion
                }
            
            entregas_por_estudiante.append({
                "estudiante": {
                    "id": estudiante.id,
                    "nombre": estudiante.nombre,
                    "apellido": estudiante.apellido,
                    "email": estudiante.email,
                    "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}"
                },
                "tiene_entrega": len(versiones_estudiante) > 0,
                "total_versiones": len(versiones_estudiante),
                "calificacion": calificacion_actual,
                "versiones": [
                    {
                        "id": v.id,
                        "numero_version": v.numero_version,
                        "descripcion": v.descripcion,
                        "fecha_subida": v.fecha_subida,
                        "es_version_actual": v.es_version_actual,
                        "tiene_archivo": v.archivo_path is not None
                    }
                    for v in versiones_estudiante
                ]
            })
        
        resultado.append({
            "proyecto_id": proyecto.id,
            "titulo": proyecto.titulo,
            "descripcion": proyecto.descripcion,
            "fecha_entrega": proyecto.fecha_entrega,
            "entregas_por_estudiante": entregas_por_estudiante
        })
    
    return {
        "curso_id": curso.id,
        "nombre_curso": curso.nombre,
        "total_proyectos": len(resultado),
        "total_estudiantes_inscritos": len(estudiante_ids),
        "entregas": resultado
    }

@app.get("/proyectos/{proyecto_id}/entregas-estudiantes")
def obtener_entregas_estudiantes_proyecto(proyecto_id: int, session: Session = Depends(get_session)):
    """Obtener todas las entregas de estudiantes para un proyecto específico.
    
    Si el proyecto está asignado a un curso, muestra las entregas de todos los estudiantes
    inscritos. Si está asignado a un estudiante individual, muestra solo sus entregas.
    Útil para profesores que necesitan revisar y calificar múltiples entregas del mismo proyecto.
    """
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    entregas_por_estudiante = []
    
    if proyecto.curso_id:
        # Proyecto asignado a curso: obtener entregas de todos los estudiantes inscritos
        stmt_estudiantes = select(CursoEstudiante).where(CursoEstudiante.curso_id == proyecto.curso_id)
        inscripciones = session.exec(stmt_estudiantes).all()
        
        for inscripcion in inscripciones:
            estudiante = session.get(Estudiante, inscripcion.estudiante_id)
            if not estudiante:
                continue
            
            # Buscar versiones subidas por este estudiante específico
            # (Nota: actualmente el modelo no guarda quién subió cada versión individualmente,
            # solo hay estudiante_id a nivel de proyecto. Para distinguir entregas por estudiante
            # necesitarías agregar estudiante_id en ProyectoVersion o crear proyectos individuales)
            versiones = crud.obtener_versiones(session, proyecto_id)
            
            # Filtrar versiones (por ahora todas se mostrarán, pero podrías crear
            # proyectos clonados por estudiante o añadir estudiante_id a ProyectoVersion)
            entregas_por_estudiante.append({
                "estudiante": {
                    "id": estudiante.id,
                    "nombre": estudiante.nombre,
                    "apellido": estudiante.apellido,
                    "email": estudiante.email,
                    "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}"
                },
                "tiene_entrega": proyecto.estudiante_id == estudiante.id,
                "versiones": [
                    {
                        "id": v.id,
                        "numero_version": v.numero_version,
                        "descripcion": v.descripcion,
                        "fecha_subida": v.fecha_subida,
                        "es_version_actual": v.es_version_actual,
                        "tiene_archivo": v.archivo_path is not None
                    }
                    for v in versiones
                ] if proyecto.estudiante_id == estudiante.id else []
            })
    else:
        # Proyecto asignado individualmente
        if proyecto.estudiante_id:
            estudiante = session.get(Estudiante, proyecto.estudiante_id)
            if estudiante:
                versiones = crud.obtener_versiones(session, proyecto_id)
                entregas_por_estudiante.append({
                    "estudiante": {
                        "id": estudiante.id,
                        "nombre": estudiante.nombre,
                        "apellido": estudiante.apellido,
                        "email": estudiante.email,
                        "nombre_completo": f"{estudiante.nombre} {estudiante.apellido}"
                    },
                    "tiene_entrega": True,
                    "versiones": [
                        {
                            "id": v.id,
                            "numero_version": v.numero_version,
                            "descripcion": v.descripcion,
                            "fecha_subida": v.fecha_subida,
                            "es_version_actual": v.es_version_actual,
                            "tiene_archivo": v.archivo_path is not None
                        }
                        for v in versiones
                    ]
                })
    
    return {
        "proyecto_id": proyecto.id,
        "titulo": proyecto.titulo,
        "descripcion": proyecto.descripcion,
        "curso_id": proyecto.curso_id,
        "fecha_entrega": proyecto.fecha_entrega,
        "total_estudiantes": len(entregas_por_estudiante),
        "entregas": entregas_por_estudiante
    }

# ==================== CALIFICACIONES ====================
@app.post("/calificaciones", response_model=CalificacionResponse)
def calificar_proyecto(calificacion: CalificarDTO, session: Session = Depends(get_session)):
    """Calificar un proyecto (solo profesores). 
    
    Soporta calificación por estudiante/versión (Moodle-style) si se proporcionan 
    estudiante_id y/o version_id en el CalificarDTO.
    """
    if calificacion.puntaje < 0 or calificacion.puntaje > 5.0:
        raise HTTPException(status_code=400, detail="Puntaje debe estar entre 0.0 y 5.0")
    
    proyecto = session.get(Proyecto, calificacion.proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Validar version_id si se proporcionó
    if hasattr(calificacion, 'version_id') and calificacion.version_id is not None:
        version = session.get(ProyectoVersion, calificacion.version_id)
        if not version or version.proyecto_id != calificacion.proyecto_id:
            raise HTTPException(status_code=400, detail="Versión no encontrada o no pertenece a este proyecto")
    
    nueva_calificacion = Calificacion(
        proyecto_id=calificacion.proyecto_id,
        profesor_id=calificacion.profesor_id,
        estudiante_id=getattr(calificacion, 'estudiante_id', None),
        version_id=getattr(calificacion, 'version_id', None),
        puntaje=calificacion.puntaje,
        comentarios=calificacion.comentarios
    )
    
    # Solo actualizar calificacion_actual del proyecto si es una calificación general (sin estudiante_id específico)
    if not hasattr(calificacion, 'estudiante_id') or calificacion.estudiante_id is None:
        proyecto.calificacion_actual = calificacion.puntaje
        session.add(proyecto)
    
    session.add(nueva_calificacion)
    session.commit()
    session.refresh(nueva_calificacion)
    
    return CalificacionResponse(
        id=nueva_calificacion.id,
        proyecto_id=nueva_calificacion.proyecto_id,
        profesor_id=nueva_calificacion.profesor_id,
        puntaje=nueva_calificacion.puntaje,
        comentarios=nueva_calificacion.comentarios,
        fecha_calificacion=nueva_calificacion.fecha_calificacion
    )

@app.get("/calificaciones/proyecto/{proyecto_id}")
def obtener_calificaciones_proyecto(proyecto_id: int, session: Session = Depends(get_session)):
    """Obtener todas las calificaciones de un proyecto"""
    calificaciones = crud.obtener_calificaciones_proyecto(session, proyecto_id)
    if not calificaciones:
        raise HTTPException(status_code=404, detail="No hay calificaciones para este proyecto")
    return [
        {
            "id": c.id,
            "puntaje": c.puntaje,
            "comentarios": c.comentarios,
            "fecha": c.fecha_calificacion
        }
        for c in calificaciones
    ]

@app.get("/calificaciones/estudiante/{estudiante_id}")
def obtener_calificaciones_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    """Obtener todas las calificaciones de un estudiante"""
    # Encontrar proyectos directamente asignados o asignados a cursos del estudiante
    stmt_direct = select(Proyecto).where(Proyecto.estudiante_id == estudiante_id)
    proyectos_direct = session.exec(stmt_direct).all()
    stmt_cursos = select(CursoEstudiante).where(CursoEstudiante.estudiante_id == estudiante_id)
    cursos_enlace = session.exec(stmt_cursos).all()
    curso_ids = [c.curso_id for c in cursos_enlace]
    proyectos_curso = []
    if curso_ids:
        stmt_c = select(Proyecto).where(Proyecto.curso_id.in_(curso_ids))
        proyectos_curso = session.exec(stmt_c).all()

    proyectos = proyectos_direct + [p for p in proyectos_curso if p not in proyectos_direct]

    todas_calificaciones = []
    for proyecto in proyectos:
        calificaciones = crud.obtener_calificaciones_proyecto(session, proyecto.id)
        for c in calificaciones:
            todas_calificaciones.append({
                "proyecto_id": proyecto.id,
                "titulo_proyecto": proyecto.titulo,
                "puntaje": c.puntaje,
                "comentarios": c.comentarios,
                "fecha": c.fecha_calificacion
            })
    
    if not todas_calificaciones:
        raise HTTPException(status_code=404, detail="No hay calificaciones para este estudiante")
    return todas_calificaciones

# ==================== REPORTES ====================
@app.get("/reportes/desempeño/estudiante/{estudiante_id}", response_model=DesempenoReporte)
def generar_reporte_desempeño(estudiante_id: int, session: Session = Depends(get_session)):
    """Generar reporte de desempeño de un estudiante"""
    statement = select(Proyecto).where(Proyecto.estudiante_id == estudiante_id)
    proyectos = session.exec(statement).all()
    
    if not proyectos:
        return DesempenoReporte(
            estudiante_id=estudiante_id,
            nombre_estudiante="Estudiante",
            promedio_calificaciones=0,
            total_proyectos=0,
            proyectos_aprobados=0,
            tasa_aprobacion=0,
            calificacion_mas_alta=0,
            calificacion_mas_baja=0,
            total_versiones=0
        )
    
    puntajes = []
    detalle = []
    total_versiones = 0
    
    for proyecto in proyectos:
        calificaciones = crud.obtener_calificaciones_proyecto(session, proyecto.id)
        versiones = crud.obtener_versiones(session, proyecto.id)
        total_versiones += len(versiones)
        
        if calificaciones:
            ultima_cal = calificaciones[0]
            puntajes.append(ultima_cal.puntaje)
            estado = "Aprobado" if ultima_cal.puntaje >= 3.0 else "Reprobado"
            detalle.append({
                "proyecto_id": proyecto.id,
                "titulo_proyecto": proyecto.titulo,
                "calificacion": ultima_cal.puntaje,
                "estado": estado,
                "versiones_cargadas": len(versiones)
            })
    
    if not puntajes:
        return DesempenoReporte(
            estudiante_id=estudiante_id,
            nombre_estudiante="Estudiante",
            promedio_calificaciones=0,
            total_proyectos=len(proyectos),
            proyectos_aprobados=0,
            tasa_aprobacion=0,
            calificacion_mas_alta=0,
            calificacion_mas_baja=0,
            total_versiones=total_versiones
        )
    
    promedio = sum(puntajes) / len(puntajes)
    aprobados = len([p for p in puntajes if p >= 3.0])
    tasa = (aprobados / len(puntajes)) * 100 if puntajes else 0
    
    return DesempenoReporte(
        estudiante_id=estudiante_id,
        nombre_estudiante="Estudiante",
        promedio_calificaciones=round(promedio, 2),
        total_proyectos=len(proyectos),
        proyectos_aprobados=aprobados,
        tasa_aprobacion=round(tasa, 2),
        calificacion_mas_alta=max(puntajes),
        calificacion_mas_baja=min(puntajes),
        total_versiones=total_versiones,
        detalle_proyectos=detalle
    )

# ==================== DEBUG ====================
@app.get("/debug/proyecto/{proyecto_id}/estudiante/{estudiante_id}")
def debug_asignacion(proyecto_id: int, estudiante_id: int, session: Session = Depends(get_session)):
    """Endpoint de depuración para verificar la asignación de un proyecto a un estudiante"""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        return {"error": "Proyecto no encontrado"}
    
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        return {"error": "Estudiante no encontrado"}
    
    info = {
        "proyecto": {
            "id": proyecto.id,
            "titulo": proyecto.titulo,
            "estudiante_id": proyecto.estudiante_id,
            "curso_id": proyecto.curso_id,
            "profesor_id": proyecto.profesor_id
        },
        "estudiante": {
            "id": estudiante.id,
            "nombre": f"{estudiante.nombre} {estudiante.apellido}",
            "email": estudiante.email
        },
        "asignacion_directa": proyecto.estudiante_id == estudiante_id,
        "cursos_estudiante": [],
        "esta_inscrito_en_curso_proyecto": False
    }
    
    # Obtener cursos del estudiante
    stmt = select(CursoEstudiante).where(CursoEstudiante.estudiante_id == estudiante_id)
    inscripciones = session.exec(stmt).all()
    for insc in inscripciones:
        curso = session.get(Curso, insc.curso_id)
        info["cursos_estudiante"].append({
            "curso_id": insc.curso_id,
            "nombre_curso": curso.nombre if curso else "N/A"
        })
        if insc.curso_id == proyecto.curso_id:
            info["esta_inscrito_en_curso_proyecto"] = True
    
    info["puede_subir_version"] = (
        info["asignacion_directa"] or 
        info["esta_inscrito_en_curso_proyecto"]
    )
    
    return info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
