# app/routers/patients.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


@router.post(
    "/",
    response_model=schemas.PatientRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient(
    patient_in: schemas.PatientCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un paciente nuevo.
    """
    existing = (
        db.query(models.Patient)
        .filter(models.Patient.document_id == patient_in.document_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un paciente con ese documento",
        )

    patient = models.Patient(
        full_name=patient_in.full_name,
        document_id=patient_in.document_id,
        birth_date=patient_in.birth_date,
        sex=patient_in.sex,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/", response_model=List[schemas.PatientRead])
def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Lista pacientes con paginación simple.
    """
    patients = (
        db.query(models.Patient)
        .order_by(models.Patient.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return patients


@router.get("/{patient_id}", response_model=schemas.PatientRead)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve un paciente por ID.
    """
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    return patient


@router.get(
    "/{patient_id}/analyses",
    response_model=List[schemas.AnalysisRead],
)
def list_analyses_for_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    """
    Lista los análisis de un paciente.
    """
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )

    analyses = (
        db.query(models.Analysis)
        .filter(models.Analysis.patient_id == patient_id)
        .order_by(models.Analysis.created_at.desc())
        .all()
    )
    return analyses
