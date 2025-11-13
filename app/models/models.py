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
    estudiante_id: Optional[int] = Field(default=None, foreign_key="estudiante.id")
    curso_id: Optional[int] = Field(default=None, foreign_key="curso.id")
    profesor_id: int = Field(foreign_key="profesor.id")
    fecha_entrega: Optional[datetime] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    version_actual: int = 1
    calificacion_actual: Optional[float] = None

class ProyectoVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    proyecto_id: int = Field(foreign_key="proyecto.id")
    estudiante_id: Optional[int] = Field(default=None, foreign_key="estudiante.id")
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
    estudiante_id: Optional[int] = Field(default=None, foreign_key="estudiante.id")
    version_id: Optional[int] = Field(default=None, foreign_key="proyectoversion.id")
    puntaje: float
    comentarios: Optional[str] = None
    fecha_calificacion: datetime = Field(default_factory=datetime.utcnow)


class Curso(SQLModel, table=True):
    """Curso creado por un profesor. Contiene relación con estudiantes."""
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None
    profesor_id: int = Field(foreign_key="profesor.id")
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)


class CursoEstudiante(SQLModel, table=True):
    """Tabla de asociación entre cursos y estudiantes"""
    id: Optional[int] = Field(default=None, primary_key=True)
    curso_id: int = Field(foreign_key="curso.id")
    estudiante_id: int = Field(foreign_key="estudiante.id")


class Tarea(SQLModel, table=True):
    """Tarea/assignment asociada a un curso"""
    id: Optional[int] = Field(default=None, primary_key=True)
    curso_id: int = Field(foreign_key="curso.id")
    titulo: str
    descripcion: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    archivo_path: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
