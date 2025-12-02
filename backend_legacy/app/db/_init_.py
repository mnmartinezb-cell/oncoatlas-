# backend/app/db/__init__.py

"""
Puente entre el paquete app.db y los módulos reales de base de datos.

Así podemos hacer:  from app.db import get_db, models, Base, engine
y por debajo se usa app.database y app.models.
"""

from ..database import Base, engine, SessionLocal, get_db
from .. import models

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "models",
]
