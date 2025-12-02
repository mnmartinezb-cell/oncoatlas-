from datetime import datetime
import json
import os
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter()

# Mini base de datos local de variantes germinales BRCA1/BRCA2
GERMLINE_DB = {
    "BRCA1": {
        "185delAG": {
            "cdna_change": "c.68_69delAG",
            "protein_change": "p.Glu23Valfs*17",
            "clinvar_id": "17661",
            "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17661/",
            "significance": "Pathogenic",
            "associated_cancer": "Cáncer de mama/ovario hereditario",
        },
        "5382insC": {
            "cdna_change": "c.5266dupC",
            "protein_change": "p.Gln1756Profs*74",
            "clinvar_id": "17664",
            "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17664/",
            "significance": "Pathogenic",
            "associated_cancer": "Cáncer de mama/ovario hereditario",
        },
    },
    "BRCA2": {
        "6174delT": {
            "cdna_change": "c.5946delT",
            "protein_change": "p.Ser1982Argfs*22",
            "clinvar_id": "37949",
            "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/37949/",
            "significance": "Pathogenic",
            "associated_cancer": "Cáncer de mama/ovario hereditario",
        },
        "2808_2811delACAA": {
            "cdna_change": "c.2808_2811delACAA",
            "protein_change": "p.Ala938Profs*21",
            "clinvar_id": "38158",
            "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/38158/",
            "significance": "Pathogenic",
            "associated_cancer": "Cáncer de mama/ovario hereditario",
        },
    },
}


def _extract_variant_from_filename(filename: str, gene: str) -> str | None:
    """
    Extrae el código de variante a partir del nombre del archivo.

    Ejemplos que funcionarán:
      BRCA1_5382insC_patient.fasta
      BRCA1_185delAG_algo.fa
      carpeta/BRCA2_6174delT_loquesea.fasta
    """
    if not filename:
        return None

    name = os.path.basename(filename)
    upper = name.upper()
    marker = gene.upper() + "_"

    idx = upper.find(marker)
    if idx == -1:
        return None

    middle = name[idx + len(marker):]

    # Cortar en el primer "_PATIENT", "_" o "." que aparezca
    for sep in ["_PATIENT", "_", "."]:
        pos = middle.upper().find(sep)
        if pos != -1:
            middle = middle[:pos]
            break

    middle = middle.strip()
    return middle or None


@router.post("/run_for_patient")
async def run_analysis_for_patient(
    patient_id: int,
    brca1_file: UploadFile = File(...),
    brca2_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Simula el análisis germinal BRCA1/BRCA2 para un paciente:

    - Verifica que el paciente exista.
    - Lee los archivos FASTA subidos.
    - Detecta variantes a partir del NOMBRE del archivo.
    - Busca esas variantes en la mini BD local GERMLINE_DB.
    - Guarda el resultado en la tabla germline_analyses.
    - Devuelve un resumen con variantes + links de ClinVar.
    """

    # 1) Verificar que el paciente exista
    patient = (
        db.query(models.Patient)
        .filter(models.Patient.id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    # 2) Leer archivos (simula análisis real, aunque aquí no usamos el contenido)
    _ = (await brca1_file.read()).decode(errors="ignore")
    _ = (await brca2_file.read()).decode(errors="ignore")

    # 3) Detectar variantes a partir de los nombres de archivo
    variants: List[dict] = []

    brca1_code = _extract_variant_from_filename(brca1_file.filename, "BRCA1")
    brca2_code = _extract_variant_from_filename(brca2_file.filename, "BRCA2")

    # BRCA1
    if brca1_code and brca1_code in GERMLINE_DB["BRCA1"]:
        v = GERMLINE_DB["BRCA1"][brca1_code]
        variants.append(
            {
                "gene": "BRCA1",
                "cdna_change": v["cdna_change"],
                "protein_change": v["protein_change"],
                "clinvar_id": v["clinvar_id"],
                "clinvar_url": v["clinvar_url"],
                "significance": v["significance"],
                "associated_cancer": v["associated_cancer"],
                "source_file": brca1_file.filename,
            }
        )

    # BRCA2
    if brca2_code and brca2_code in GERMLINE_DB["BRCA2"]:
        v = GERMLINE_DB["BRCA2"][brca2_code]
        variants.append(
            {
                "gene": "BRCA2",
                "cdna_change": v["cdna_change"],
                "protein_change": v["protein_change"],
                "clinvar_id": v["clinvar_id"],
                "clinvar_url": v["clinvar_url"],
                "significance": v["significance"],
                "associated_cancer": v["associated_cancer"],
                "source_file": brca2_file.filename,
            }
        )

    # 4) Resumen
    if variants:
        summary = (
            f"Se detectaron {len(variants)} variantes germinales patogénicas "
            "conocidas en BRCA1/BRCA2."
        )
    else:
        summary = (
            "No se detectaron variantes germinales patogénicas conocidas en "
            "BRCA1/BRCA2."
        )

    payload = {
        "analysis_id": None,
        "patient_id": patient_id,
        "summary": summary,
        "variants": variants,
    }

    # 5) Guardar en la tabla germline_analyses
    row = models.GermlineAnalysis(
        patient_id=patient_id,
        description="Análisis germinal BRCA1/BRCA2",
        created_at=datetime.utcnow(),
        summary=summary,
        raw_result=json.dumps(payload, ensure_ascii=False),
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    payload["analysis_id"] = row.id

    return payload
