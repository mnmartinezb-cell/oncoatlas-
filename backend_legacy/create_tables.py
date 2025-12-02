# backend/create_tables.py

from app.database import Base, engine
from app import models  # importa para que los modelos se registren

print("Creando tablas en oncoatlas.db...")
Base.metadata.create_all(bind=engine)
print("Listo.")
