from sqlmodel import select
from app.models.models import Proyecto, ProyectoVersion, Calificacion


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
