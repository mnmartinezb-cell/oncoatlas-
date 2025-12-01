# backend/app/schemas.py

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, ConfigDict


# ============================================================
# BASE GENÉRICA PARA OBJETOS ORM
# ============================================================

class ORMModel(BaseModel):
    """
    Base para modelos que se construyen a partir de objetos ORM
    (SQLAlchemy). Equivalente al antiguo `orm_mode = True`.
    """
    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ESQUEMAS DE DOCTOR
# ============================================================

class DoctorBase(BaseModel):
    name: str
    email: EmailStr
    specialty: Optional[str] = None


class DoctorCreate(DoctorBase):
    # Esquema de entrada para crear médico (admin)
    is_admin: bool = False


class Doctor(DoctorBase, ORMModel):
    # Esquema principal de salida para médicos
    id: int
    is_admin: bool


class DoctorRead(Doctor):
    """
    Alias de compatibilidad para los routers que utilizan
    `schemas.DoctorRead` como response_model.
    """
    pass


# ============================================================
# ESQUEMAS DE PACIENTE
# ============================================================

class PatientBase(BaseModel):
    # Nombres de campos según el OpenAPI (/docs)
    full_name: str
    document_id: str
    sex: str
    date_of_birth: date


class PatientCreate(PatientBase):
    pass


class Patient(PatientBase, ORMModel):
    id: int
    doctor_id: int


class PatientRead(Patient):
    """
    Alias de compatibilidad por si algún router usa PatientRead.
    """
    pass


# ============================================================
# ESQUEMAS DE ANÁLISIS GERMINAL Y VARIANTES
# ============================================================

class ClinVarInfo(BaseModel):
    """
    Información clínica mínima que guardamos localmente para
    enlazar con ClinVar.
    """
    clinvar_id: Optional[str] = None            # p.ej. "VCV000009365"
    clinical_significance: Optional[str] = None # "Pathogenic", etc.
    review_status: Optional[str] = None         # "criteria provided, multiple submitters..."
    condition: Optional[str] = None             # "Breast-ovarian cancer, familial 2"
    clinvar_url: Optional[str] = None           # URL directa a ClinVar


class VariantSummary(ClinVarInfo):
    """
    Variante ya “interpretada” desde el punto de vista clínico.
    Esto es lo que usamos tanto en el JSON como en el PDF.
    """
    gene: str                                   # BRCA1 / BRCA2
    position: int                               # posición 1-based en la referencia
    ref: str
    alt: str
    type: str                                   # "SNV", "indel", etc.


class AnalysisBase(BaseModel):
    """
    Representación lógica de un análisis almacenado en la BD.
    """
    patient_id: int
    status: str                                 # "completed", "failed", etc.
    summary: str                                # resumen en lenguaje natural
    details: Dict[str, Any]                     # conteos, variantes, etc.


class AnalysisCreate(AnalysisBase):
    """
    Esquema para crear un análisis desde el backend.
    """
    pass


class Analysis(AnalysisBase, ORMModel):
    """
    Esquema completo que FastAPI usa como response_model cuando
    devolvemos un análisis ya guardado en la BD.
    """
    id: int
    created_at: datetime


class AnalysisRead(Analysis):
    """
    Alias de compatibilidad para routers que usen AnalysisRead.
    """
    pass


class GermlineRunResult(BaseModel):
    """
    Respuesta del endpoint:
    POST /patients/{patient_id}/analyses/run-germline

    Incluye:
    - el análisis guardado en la BD (Analysis)
    - resumen numérico
    - listas de variantes clasificadas.
    """
    analysis: Analysis
    total_snv_brca1: int
    total_snv_brca2: int
    pathogenic_variants: List[VariantSummary] = []
    likely_pathogenic_variants: List[VariantSummary] = []
    vus_variants: List[VariantSummary] = []
