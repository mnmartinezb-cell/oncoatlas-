from app.database import engine
from app import models

if __name__ == "__main__":
    print("Creando tablas en la base de datos...")
    models.Base.metadata.create_all(bind=engine)
    print("Listo.")
