# backend/app/routers/patients.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    tags=["patients"],
)


@router.get(
    "/doctors/{doctor_id}/patients",
    response_model=List[schemas.PatientRead],
)
def list_patients_for_doctor(
    doctor_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """Lista de pacientes de un médico concreto."""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico no encontrado",
        )

    patients = (
        db.query(models.Patient)
        .filter(models.Patient.doctor_id == doctor_id)
        .order_by(models.Patient.id)
        .all()
    )
    return patients


@router.post(
    "/doctors/{doctor_id}/patients",
    response_model=schemas.PatientRead,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_for_doctor(
    patient_in: schemas.PatientCreate,
    doctor_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """Crear un paciente asociado a un médico."""
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Médico no encontrado",
        )

    patient = models.Patient(
        full_name=patient_in.full_name,
        document_id=patient_in.document_id,
        date_of_birth=patient_in.date_of_birth,
        sex=patient_in.sex,
        doctor_id=doctor_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get(
    "/patients/{patient_id}",
    response_model=schemas.PatientRead,
)
def get_patient(
    patient_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """Detalle de un paciente concreto."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )
    return patient
