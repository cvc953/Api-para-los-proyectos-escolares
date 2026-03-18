import os
from sqlmodel import SQLModel, create_engine, Session

# Read database URL from environment. Example MySQL URL:
#  mysql+pymysql://user:password@host:3306/dbname?charset=utf8mb4
# For PostgreSQL (Neon, Supabase, etc.):
#  postgresql+psycopg://user:password@host/dbname
# Or simply: postgresql://user:password@host/dbname (sqlalchemy will auto-detect)
# Defaults to a local SQLite file for development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./plataforma_proyectos.db")

# For MySQL/PostgreSQL, enable pool_pre_ping to avoid stale connection errors.
# Use psycopg for PostgreSQL connections.
if DATABASE_URL.startswith("postgresql"):
    # Use psycopg (v3) driver
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
elif DATABASE_URL.startswith("mysql"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create database tables from SQLModel models."""
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        # In Vercel serverless, tables might already exist or be managed externally


def get_session():
    """Yield a DB session (can be used as a FastAPI dependency)."""
    with Session(engine) as session:
        yield session
