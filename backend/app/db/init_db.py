from app.db.database import Base, engine
from app.db import models  # esto importa los modelos para que Base los conozca


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("✔ Tablas creadas en oncoatlas.db")


if __name__ == "__main__":
    init_db()
