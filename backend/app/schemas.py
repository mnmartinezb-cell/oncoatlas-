# app/schemas.py

from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel


# ===================== PACIENTES =====================

class PatientBase(BaseModel):
    full_name: str
    document_id: str
    birth_date: Optional[date] = None
    sex: Optional[str] = None


class PatientCreate(PatientBase):
    """Esquema para crear paciente."""
    pass


class PatientRead(PatientBase):
    """Esquema para leer/mostrar paciente."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ===================== MUTACIONES =====================

class MutationRead(BaseModel):
    id: int
    gene: str
    hgvs_c: str
    significance: str
    source: Optional[str] = None

    class Config:
        orm_mode = True


# ===================== ANÁLISIS =====================

class AnalysisBase(BaseModel):
    overall_risk: str


class AnalysisRead(AnalysisBase):
    id: int
    patient_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class AnalysisDetail(AnalysisRead):
    mutations: List[MutationRead] = []

    class Config:
        orm_mode = True


# ===================== PACIENTE + SUS ANÁLISIS =====================

class PatientWithAnalyses(PatientRead):
    analyses: List[AnalysisRead] = []

    class Config:
        orm_mode = True
