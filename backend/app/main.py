from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import patients, analysis

# Crear tablas (patients + germline_analyses)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oncoatlas Backend - Pacientes + Análisis Germinal")

# CORS abierto para pruebas locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Oncoatlas backend con pacientes y análisis germinal funcionando"}


# Rutas
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
