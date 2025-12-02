from typing import Optional

from pydantic import BaseModel


# ======================
# Esquemas de Pacientes
# ======================

class PatientBase(BaseModel):
    full_name: str
    document_number: str
    age: Optional[int] = None
    gender: Optional[str] = None


class PatientCreate(PatientBase):
    # El médico que crea / al que pertenece el paciente
    doctor_id: int


class PatientOut(PatientBase):
    id: int
    doctor_id: int

    class Config:
        orm_mode = True  # permite convertir desde objetos SQLAlchemy


# ====================
# Esquemas de Médicos
# ====================

class DoctorBase(BaseModel):
    full_name: str
    email: str
    specialty: Optional[str] = None


class DoctorCreate(DoctorBase):
    pass


class DoctorOut(DoctorBase):
    id: int

    class Config:
        orm_mode = True
