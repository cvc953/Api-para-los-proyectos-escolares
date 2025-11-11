from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Estudiante(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    email: str
    password_hash: Optional[str] = None

class Profesor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    apellido: str
    email: str
    password_hash: Optional[str] = None

class Proyecto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    descripcion: Optional[str] = None
    estudiante_id: int = Field(foreign_key="estudiante.id")
    profesor_id: int = Field(foreign_key="profesor.id")
    fecha_entrega: Optional[datetime] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    version_actual: int = 1
    calificacion_actual: Optional[float] = None

class ProyectoVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    proyecto_id: int = Field(foreign_key="proyecto.id")
    numero_version: int
    archivo_path: Optional[str] = None
    tamano_archivo: Optional[int] = None
    descripcion: Optional[str] = None
    fecha_subida: datetime = Field(default_factory=datetime.utcnow)
    es_version_actual: bool = True

class Calificacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    proyecto_id: int = Field(foreign_key="proyecto.id")
    profesor_id: int = Field(foreign_key="profesor.id")
    puntaje: float
    comentarios: Optional[str] = None
    fecha_calificacion: datetime = Field(default_factory=datetime.utcnow)
