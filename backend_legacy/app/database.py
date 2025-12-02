from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Usa el nombre de archivo que prefieras para la BD
SQLALCHEMY_DATABASE_URL = "sqlite:///./oncoatlas.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario para SQLite en FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
