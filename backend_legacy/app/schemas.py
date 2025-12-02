from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


# ---------- Pacientes ----------

class PatientBase(BaseModel):
    full_name: str
    document_number: str
    age: Optional[int] = None
    gender: Optional[str] = None
    doctor_id: Optional[int] = None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    id: int

    class Config:
        orm_mode = True


# ---------- Doctores ----------

class DoctorBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    specialty: Optional[str] = None


class DoctorCreate(DoctorBase):
    pass


class DoctorOut(DoctorBase):
    id: int

    class Config:
        orm_mode = True


# ---------- Análisis germinal ----------

class GermlineVariantOut(BaseModel):
    gene: str
    cdna_change: str
    clinvar_id: str
    clinvar_url: str
    significance: str
    associated_cancer: str


class GermlineAnalysisOut(BaseModel):
    id: int
    patient_id: int
    description: str
    created_at: datetime
    summary: str
    variants: List[GermlineVariantOut]

    class Config:
        orm_mode = True

