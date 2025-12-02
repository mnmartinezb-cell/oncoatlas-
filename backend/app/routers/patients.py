from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.PatientOut])
def list_patients(db: Session = Depends(get_db)):
    """
    Lista todos los pacientes.
    """
    patients = db.query(models.Patient).all()
    return patients


@router.post("/", response_model=schemas.PatientOut, status_code=201)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """
    Crea un paciente nuevo.
    Valida que no se repita el número de documento.
    """
    existing = (
        db.query(models.Patient)
        .filter(models.Patient.document_number == patient.document_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un paciente con ese número de documento.",
        )

    db_patient = models.Patient(
        full_name=patient.full_name,
        document_number=patient.document_number,
        age=patient.age,
        gender=patient.gender,
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("/{patient_id}/analyses")
def list_patient_analyses(patient_id: int, db: Session = Depends(get_db)):
    """
    Lista los análisis germinales asociados a un paciente.

    Devuelve el JSON completo guardado en raw_result si está disponible.
    """
    patient = (
        db.query(models.Patient)
        .filter(models.Patient.id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    rows = (
        db.query(models.GermlineAnalysis)
        .filter(models.GermlineAnalysis.patient_id == patient_id)
        .order_by(models.GermlineAnalysis.created_at.desc())
        .all()
    )

    result = []
    for r in rows:
        if r.raw_result:
            try:
                payload = json.loads(r.raw_result)
                payload["analysis_id"] = r.id
                result.append(payload)
                continue
            except json.JSONDecodeError:
                pass

        # Si no hay JSON válido, devolver algo básico
        result.append(
            {
                "analysis_id": r.id,
                "patient_id": r.patient_id,
                "description": r.description,
                "summary": r.summary,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )

    return result

