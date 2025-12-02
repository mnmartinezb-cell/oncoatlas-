# backend/app/crud.py

from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import Patient, Analysis, Variant


# --------- Helpers de sesión (opcional, por si quieres usarlos en scripts) ---------

def get_db() -> Session:
    """Devuelve una sesión de BD; pensada para usar con Depends en FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------- Pacientes ---------

def get_or_create_patient(
    db: Session,
    *,
    full_name: str,
    document_id: Optional[str] = None,
) -> Patient:
    """
    Busca un paciente por document_id (si lo hay) o por nombre.
    Si no existe, lo crea.
    """

    query = db.query(Patient)

    if document_id:
        patient = query.filter(Patient.document_id == document_id).first()
    else:
        patient = query.filter(Patient.full_name == full_name).first()

    if patient:
        return patient

    patient = Patient(full_name=full_name, document_id=document_id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


# --------- Análisis + variantes ---------

def create_analysis_with_mutations(
    db: Session,
    *,
    patient: Patient,
    mutations: List[dict],
) -> Analysis:
    """
    Crea un registro de Analysis y sus Variant asociadas
    a partir de la lista de 'mutations' que devuelve tu motor de análisis.
    """

    analysis = Analysis(patient_id=patient.id, num_mutations=len(mutations))
    db.add(analysis)
    db.flush()  # para que analysis.id exista antes de crear variantes

    for mut in mutations:
        conditions = mut.get("conditions")
        # lo guardamos como texto simple; si es lista, la unimos con "; "
        if isinstance(conditions, list):
            conditions_str = "; ".join(str(c) for c in conditions)
        else:
            conditions_str = str(conditions) if conditions is not None else None

        variant = Variant(
            analysis_id=analysis.id,
            gene=mut.get("gene") or "",
            source_file=mut.get("source_file") or "",
            clinvar_id=str(mut.get("clinvar_id")) if mut.get("clinvar_id") else None,
            hgvs_c=mut.get("hgvs_c"),
            hgvs_p=mut.get("hgvs_p"),
            clinical_significance=mut.get("clinical_significance"),
            conditions=conditions_str,
            raw_json=json.dumps(mut, ensure_ascii=False),
        )
        db.add(variant)

    db.commit()
    db.refresh(analysis)
    return analysis
