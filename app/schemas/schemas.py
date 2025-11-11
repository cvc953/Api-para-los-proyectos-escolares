from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ProyectoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    estudiante_id: int
    profesor_id: int
    fecha_entrega: Optional[datetime] = None
    nombre_archivo: Optional[str] = None
    comentarios_version: Optional[str] = None

class ProyectoResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    estudiante_id: int
    profesor_id: int
    fecha_entrega: Optional[datetime]
    fecha_creacion: datetime
    version_actual: int
    calificacion_actual: Optional[float]
    total_versiones: int = 0

class CalificarDTO(BaseModel):
    proyecto_id: int
    profesor_id: int
    puntaje: float
    comentarios: Optional[str] = None

class CalificacionResponse(BaseModel):
    id: int
    proyecto_id: int
    profesor_id: int
    puntaje: float
    comentarios: Optional[str]
    fecha_calificacion: datetime

class DesempenoReporte(BaseModel):
    estudiante_id: int
    nombre_estudiante: str
    promedio_calificaciones: float
    total_proyectos: int
    proyectos_aprobados: int
    tasa_aprobacion: float
    calificacion_mas_alta: float
    calificacion_mas_baja: float
    total_versiones: int
    detalle_proyectos: List[dict] = []
