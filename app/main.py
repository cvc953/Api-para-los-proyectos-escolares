from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
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
    statement = select(Estudiante).where(Estudiante.email == email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(password, user.password_hash or ""):
        statement = select(Profesor).where(Profesor.email == email)
        user = session.exec(statement).first()
        if not user or not verify_password(password, user.password_hash or ""):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_access_token(data={"sub": user.email, "id": user.id})
    return {"access_token": token, "token_type": "bearer", "usuario_id": user.id}

# ==================== PROYECTOS ====================
@app.post("/proyectos", response_model=ProyectoResponse)
def crear_proyecto(proyecto: ProyectoCreate, session: Session = Depends(get_session)):
    """Crear nuevo proyecto"""
    # Validar que estudiante y profesor existen
    estudiante = session.get(Estudiante, proyecto.estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=400, detail="Estudiante no encontrado")
    profesor = session.get(Profesor, proyecto.profesor_id)
    if not profesor:
        raise HTTPException(status_code=400, detail="Profesor no encontrado")

    nuevo_proyecto = Proyecto(
        titulo=proyecto.titulo,
        descripcion=proyecto.descripcion,
        estudiante_id=proyecto.estudiante_id,
        profesor_id=proyecto.profesor_id,
        fecha_entrega=proyecto.fecha_entrega,
        version_actual=1,
        calificacion_actual=None
    )
    try:
        session.add(nuevo_proyecto)
        session.commit()
        session.refresh(nuevo_proyecto)

        # Crear primera versión
        primera_version = ProyectoVersion(
            proyecto_id=nuevo_proyecto.id,
            numero_version=1,
            archivo_path=proyecto.nombre_archivo,
            descripcion=proyecto.comentarios_version,
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
        # Intentar rollback y devolver un error legible
        try:
            session.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al crear proyecto: {str(e)}")

@app.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(proyecto_id: int, session: Session = Depends(get_session)):
    """Obtener detalle de un proyecto"""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    versiones = crud.obtener_versiones(session, proyecto_id)
    return ProyectoResponse(
        id=proyecto.id,
        titulo=proyecto.titulo,
        descripcion=proyecto.descripcion,
        estudiante_id=proyecto.estudiante_id,
        profesor_id=proyecto.profesor_id,
        fecha_entrega=proyecto.fecha_entrega,
        fecha_creacion=proyecto.fecha_creacion,
        version_actual=proyecto.version_actual,
        calificacion_actual=proyecto.calificacion_actual,
        total_versiones=len(versiones)
    )

@app.get("/proyectos/estudiante/{estudiante_id}")
def obtener_proyectos_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    """Listar todos los proyectos de un estudiante"""
    statement = select(Proyecto).where(Proyecto.estudiante_id == estudiante_id)
    proyectos = session.exec(statement).all()
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

# ==================== VERSIONES ====================
@app.post("/proyectos/{proyecto_id}/versiones")
def subir_version(proyecto_id: int, descripcion: str, session: Session = Depends(get_session)):
    """Subir nueva versión de un proyecto"""
    proyecto = session.get(Proyecto, proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Marcar versiones anteriores como no actuales
    versiones = crud.obtener_versiones(session, proyecto_id)
    for v in versiones:
        v.es_version_actual = False
    
    # Crear nueva versión
    nueva_version = ProyectoVersion(
        proyecto_id=proyecto_id,
        numero_version=len(versiones) + 1,
        descripcion=descripcion,
        es_version_actual=True
    )
    
    proyecto.version_actual = nueva_version.numero_version
    
    session.add(nueva_version)
    session.add(proyecto)
    session.commit()
    session.refresh(nueva_version)
    
    return {"id": nueva_version.id, "numero_version": nueva_version.numero_version, "fecha": nueva_version.fecha_subida}

@app.get("/proyectos/{proyecto_id}/versiones")
def obtener_versiones_proyecto(proyecto_id: int, session: Session = Depends(get_session)):
    """Obtener historial de versiones de un proyecto"""
    versiones = crud.obtener_versiones(session, proyecto_id)
    if not versiones:
        raise HTTPException(status_code=404, detail="No hay versiones para este proyecto")
    return [
        {
            "id": v.id,
            "numero_version": v.numero_version,
            "descripcion": v.descripcion,
            "fecha_subida": v.fecha_subida,
            "es_version_actual": v.es_version_actual
        }
        for v in versiones
    ]

# ==================== CALIFICACIONES ====================
@app.post("/calificaciones", response_model=CalificacionResponse)
def calificar_proyecto(calificacion: CalificarDTO, session: Session = Depends(get_session)):
    """Calificar un proyecto (solo profesores)"""
    if calificacion.puntaje < 0 or calificacion.puntaje > 5.0:
        raise HTTPException(status_code=400, detail="Puntaje debe estar entre 0.0 y 5.0")
    
    proyecto = session.get(Proyecto, calificacion.proyecto_id)
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    nueva_calificacion = Calificacion(
        proyecto_id=calificacion.proyecto_id,
        profesor_id=calificacion.profesor_id,
        puntaje=calificacion.puntaje,
        comentarios=calificacion.comentarios
    )
    
    proyecto.calificacion_actual = calificacion.puntaje
    
    session.add(nueva_calificacion)
    session.add(proyecto)
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
    statement = select(Proyecto).where(Proyecto.estudiante_id == estudiante_id)
    proyectos = session.exec(statement).all()
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
