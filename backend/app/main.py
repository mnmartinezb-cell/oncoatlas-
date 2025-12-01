# backend/app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import doctors, patients, analyses, reports


# -------------------------------------------------------------------
# Inicialización de la base de datos
# -------------------------------------------------------------------

# Crea todas las tablas definidas en app.models si no existen.
Base.metadata.create_all(bind=engine)


# -------------------------------------------------------------------
# Aplicación FastAPI
# -------------------------------------------------------------------

app = FastAPI(
    title="Oncoatlas API",
    description=(
        "API local de Oncoatlas para gestión de médicos, pacientes y "
        "análisis germinales BRCA1/BRCA2 con reporte en PDF."
    ),
    version="0.9.0-germline-demo",
)


# -------------------------------------------------------------------
# CORS (para que el frontend en HTML/JS pueda llamar al backend)
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # para uso local y académico, sin problemas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Rutas básicas
# -------------------------------------------------------------------

@app.get("/", tags=["root"])
def read_root():
    """
    Endpoint básico de prueba.
    Sirve para comprobar que el backend está arriba.
    """
    return {
        "app": "Oncoatlas",
        "status": "ok",
        "message": "API germinal BRCA1/BRCA2 de Oncoatlas en ejecución.",
        "version": app.version,
    }


# -------------------------------------------------------------------
# Inclusión de routers
# -------------------------------------------------------------------

# CRUD de médicos y asignación de pacientes a médicos
app.include_router(doctors.router)

# CRUD de pacientes
app.include_router(patients.router)

# Ejecución de análisis germinal BRCA1/BRCA2
app.include_router(analyses.router)

# Generación de informes PDF a partir de los análisis
app.include_router(reports.router)
