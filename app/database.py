import os
from sqlmodel import SQLModel, create_engine, Session

# Read database URL from environment. Example MySQL URL:
#  mysql+pymysql://user:password@host:3306/dbname?charset=utf8mb4
# Defaults to a local SQLite file for development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plataforma_proyectos.db")

# For MySQL (using PyMySQL), enable pool_pre_ping to avoid stale connection errors.
# SQLModel's create_engine simply forwards options to SQLAlchemy.
if DATABASE_URL.startswith("mysql"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create database tables from SQLModel models."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a DB session (can be used as a FastAPI dependency)."""
    with Session(engine) as session:
        yield session
