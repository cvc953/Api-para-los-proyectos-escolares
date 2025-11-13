from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ProyectoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    estudiante_id: Optional[int]
    curso_id: Optional[int]
    profesor_id: int
    fecha_entrega: Optional[datetime] = None
    nombre_archivo: Optional[str] = None
    comentarios_version: Optional[str] = None

class ProyectoResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    estudiante_id: Optional[int]
    curso_id: Optional[int] = None
    profesor_id: int
    fecha_entrega: Optional[datetime]
    fecha_creacion: datetime
    version_actual: int
    calificacion_actual: Optional[float]
    total_versiones: int = 0
    # Indica, si la petición incluye un token, si el estudiante autenticado
    # está asignado a este proyecto (como propietario directo o inscrito en el curso).
    es_estudiante_asignado: Optional[bool] = None

class CalificarDTO(BaseModel):
    proyecto_id: int
    profesor_id: int
    estudiante_id: Optional[int] = None  # Para calificar a un estudiante específico (Moodle-style)
    version_id: Optional[int] = None  # Para calificar una versión específica
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


class CursoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    profesor_id: int


class CursoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    profesor_id: int
    fecha_creacion: datetime


class AddStudentDTO(BaseModel):
    curso_id: int
    estudiante_id: int


class TareaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha_entrega: Optional[datetime] = None


class TareaResponse(BaseModel):
    id: int
    curso_id: int
    titulo: str
    descripcion: Optional[str]
    fecha_entrega: Optional[datetime]
    fecha_creacion: datetime
