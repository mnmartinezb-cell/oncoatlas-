from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    """
    Lista todos los médicos registrados.
    """
    doctors = db.query(models.Doctor).all()
    return doctors


@router.post("/", response_model=schemas.DoctorOut, status_code=201)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    """
    Crea un médico nuevo.
    Valida que no se repita el correo electrónico.
    """
    existing = (
        db.query(models.Doctor)
        .filter(models.Doctor.email == doctor.email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un médico con ese correo electrónico.",
        )

    db_doctor = models.Doctor(
        full_name=doctor.full_name,
        email=doctor.email,
        specialty=doctor.specialty,
    )
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor
