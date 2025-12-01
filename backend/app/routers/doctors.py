# backend/app/routers/doctors.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.post(
    "/doctors",
    response_model=schemas.DoctorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_doctor(
    doctor_in: schemas.DoctorCreate,
    db: Session = Depends(get_db),
):
    """Crear un nuevo médico (usuario)."""

    existing = db.query(models.Doctor).filter(models.Doctor.email == doctor_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un médico con ese correo electrónico.",
        )

    doctor = models.Doctor(
        name=doctor_in.name,
        email=doctor_in.email,
        specialty=doctor_in.specialty,
        is_admin=doctor_in.is_admin,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get(
    "/doctors",
    response_model=List[schemas.DoctorRead],
)
def list_doctors(db: Session = Depends(get_db)):
    """Listar todos los médicos registrados."""
    doctors = db.query(models.Doctor).order_by(models.Doctor.id).all()
    return doctors
