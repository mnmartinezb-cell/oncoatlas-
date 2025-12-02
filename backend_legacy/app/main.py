from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine          # 👈 OJO: app.database, NO app.db
from app.routers import patients, doctors, analysis

# Crea TODAS las tablas definidas en app.models (incluyendo germline_analyses)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Oncoatlas API")

# CORS sencillo para pruebas locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Oncoatlas backend running"}


# Rutas principales
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
