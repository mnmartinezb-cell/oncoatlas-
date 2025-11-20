# backend/app/test_db.py

from sqlalchemy import text
from app.db.database import SessionLocal, engine, Base


def main() -> None:
    print("=== Probando módulo de base de datos de ONCOATLAS ===")

    # 1) Mostrar info básica del motor
    print("URL del engine:", engine.url)

    # 2) Ver qué tablas conoce SQLAlchemy por metadata
    print("\nTablas en Base.metadata:")
    for name in Base.metadata.tables.keys():
        print("  -", name)

    # 3) Abrir sesión y preguntar directamente a SQLite
    db = SessionLocal()
    try:
        print("\nTablas reales en el archivo oncoatlas.db:")
        result = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        for row in result:
            print("  -", row[0])
    finally:
        db.close()

    print("\n✅ Prueba de base de datos completada.")


if __name__ == "__main__":
    main()
