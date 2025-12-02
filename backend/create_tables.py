from app.database import Base, engine
from app import models


def create_db_and_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_db_and_tables()
