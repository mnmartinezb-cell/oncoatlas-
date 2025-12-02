# backend/app/routers/doctors.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(
    prefix="/doctors",
    tags=["doctors"],
)


# -------------------------
# Dependencia de base de datos
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Esquemas Pydantic
# -------------------------
class DoctorBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    specialty: Optional[str] = None


class DoctorCreate(DoctorBase):
    pass


class DoctorRead(DoctorBase):
    id: int

    class Config:
        orm_mode = True


# -------------------------
# Endpoints
# -------------------------
@router.post("/", response_model=DoctorRead)
def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo médico.
    Solo se asignan los campos que realmente existan en models.Doctor.
    """
    db_doctor = models.Doctor()
    for field, value in doctor.dict().items():
        if hasattr(db_doctor, field):
            setattr(db_doctor, field, value)

    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor


@router.get("/", response_model=List[DoctorRead])
def list_doctors(db: Session = Depends(get_db)):
    """
    Lista todos los médicos registrados.
    """
    doctors = db.query(models.Doctor).all()
    return doctors

