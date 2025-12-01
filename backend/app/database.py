# backend/app/database.py

"""
Módulo de conexión a la base de datos para Oncoatlas.

- Usa SQLite como base de datos local.
- Crea el engine, la sesión (SessionLocal) y la clase Base para los modelos.
- Expone la dependencia get_db() para FastAPI.
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carpeta donde se guardará el archivo de la base de datos
DB_DIR = Path("db")
DB_DIR.mkdir(exist_ok=True)

# Ruta del archivo SQLite (por ejemplo: backend/db/oncoatlas.db)
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/oncoatlas.db"

# Crear el engine de SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario para SQLite en un solo hilo
)

# Creador de sesiones de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para los modelos (ORM)
Base = declarative_base()


def get_db():
    """
    Dependencia para FastAPI.

    Abre una sesión de base de datos al inicio del request
    y la cierra automáticamente al final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
