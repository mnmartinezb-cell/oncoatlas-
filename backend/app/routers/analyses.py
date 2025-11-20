# app/routers/analyses.py

import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app import models, schemas
from app.services.analysis import run_germline_analysis

router = APIRouter(
    prefix="/analyses",
    tags=["Analyses"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_upload_tmp(file: UploadFile) -> str:
    """
    Guarda el archivo subido en la carpeta uploads/ y devuelve la ruta.
    """
    if not file.filename:
        ext = ""
    else:
        _, ext = os.path.splitext(file.filename)

    tmp_name = f"{uuid.uuid4().hex}{ext}"
    tmp_path = os.path.join(UPLOAD_DIR, tmp_name)

    with open(tmp_path, "wb") as f:
        f.write(file.file.read())

    return tmp_path


@router.post(
    "/patients/{patient_id}",
    response_model=schemas.AnalysisDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis_for_patient(
    patient_id: int,
    brca1_file: UploadFile = File(...),
    brca2_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Recibe FASTA de BRCA1 y BRCA2, corre el análisis germinal,
    guarda el análisis y las mutaciones en la BD y devuelve el informe.
    """
    # 1. Verificar paciente
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado",
        )

    # 2. Guardar archivos temporalmente
    brca1_path = _save_upload_tmp(brca1_file)
    brca2_path = _save_upload_tmp(brca2_file)

    # 3. Ejecutar análisis
    result = run_germline_analysis(brca1_path, brca2_path)

    # (Opcional) borrar archivos temporales si quieres
    # os.remove(brca1_path)
    # os.remove(brca2_path)

    # 4. Crear Analysis
    analysis = models.Analysis(
        patient_id=patient.id,
        created_at=result["created_at"],
        overall_risk=result["overall_risk"],
    )
    db.add(analysis)
    db.flush()  # Para tener analysis.id

    # 5. Crear Mutations
    for mut in result["mutations"]:
        mutation = models.Mutation(
            analysis_id=analysis.id,
            gene=mut["gene"],
            hgvs_c=mut["hgvs_c"],
            significance=mut["significance"],
            source=mut.get("source"),
        )
        db.add(mutation)

    db.commit()
    db.refresh(analysis)

    # 6. Devolver análisis con mutaciones (AnalysisDetail)
    return analysis


@router.get(
    "/{analysis_id}",
    response_model=schemas.AnalysisDetail,
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Devuelve un análisis con sus mutaciones.
    """
    analysis = (
        db.query(models.Analysis)
        .filter(models.Analysis.id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis no encontrado",
        )
    return analysis
