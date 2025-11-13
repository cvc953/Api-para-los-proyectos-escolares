from sqlmodel import select
from app.models.models import Proyecto, ProyectoVersion, Calificacion
from app.models.models import Curso, CursoEstudiante, Tarea


def crear_proyecto(session, proyecto: Proyecto):
    session.add(proyecto)
    session.commit()
    session.refresh(proyecto)
    return proyecto


def crear_version(session, version: ProyectoVersion):
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def obtener_versiones(session, proyecto_id: int):
    statement = select(ProyectoVersion).where(ProyectoVersion.proyecto_id == proyecto_id).order_by(ProyectoVersion.numero_version.desc())
    return session.exec(statement).all()


def calificar_proyecto(session, calificacion: Calificacion):
    session.add(calificacion)
    session.commit()
    session.refresh(calificacion)
    return calificacion


def obtener_calificaciones_proyecto(session, proyecto_id: int):
    statement = select(Calificacion).where(Calificacion.proyecto_id == proyecto_id).order_by(Calificacion.fecha_calificacion.desc())
    return session.exec(statement).all()


def crear_curso(session, curso: Curso):
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return curso


def agregar_estudiante_a_curso(session, enlace: CursoEstudiante):
    session.add(enlace)
    session.commit()
    session.refresh(enlace)
    return enlace


def obtener_cursos_por_profesor(session, profesor_id: int):
    statement = select(Curso).where(Curso.profesor_id == profesor_id).order_by(Curso.fecha_creacion.desc())
    return session.exec(statement).all()


def crear_tarea(session, tarea: Tarea):
    session.add(tarea)
    session.commit()
    session.refresh(tarea)
    return tarea


def obtener_tareas_por_curso(session, curso_id: int):
    statement = select(Tarea).where(Tarea.curso_id == curso_id).order_by(Tarea.fecha_creacion.desc())
    return session.exec(statement).all()
