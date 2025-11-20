# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine
from app import models
from app.routers import patients, analyses

app = FastAPI(
    title="Oncoatlas Germinal",
    version="0.1.0",
    description="API local para análisis germinal de BRCA1/BRCA2.",
)

# CORS (por si el frontend está en otro puerto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # luego puedes restringirlo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """
    Crea las tablas en la BD si no existen.
    """
    models.Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Oncoatlas Germinal API funcionando"}


# Incluir routers
app.include_router(patients.router)
app.include_router(analyses.router)
