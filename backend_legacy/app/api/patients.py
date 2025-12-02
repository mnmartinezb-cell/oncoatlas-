# backend/app/api/patients.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# 👇 IMPORT CORRECTO: usamos el módulo de base de datos que está en app/db/database.py
from app.db.database import SessionLocal
from app.models import Patient
from app.schemas import PatientCreate, PatientResponse

router = APIRouter(
    prefix="/patients",
    tags=["patients"],
)


# ----- Dependencia de sesión de BD -----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----- Endpoints -----

@router.get("/", response_model=List[PatientResponse])
def list_patients(db: Session = Depends(get_db)):
    """
    Listar todos los pacientes registrados en la base de datos.
    """
    patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
    return patients


@router.post(
    "/create",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    """
    Crear un nuevo paciente.
    - Valida que no exista ya un paciente con el mismo email.
    """
    existing = db.query(Patient).filter(Patient.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un paciente con ese correo.",
        )

    patient = Patient(
        full_name=payload.full_name,
        email=payload.email,
        document_id=payload.document_id,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient
