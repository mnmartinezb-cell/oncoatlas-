from typing import List, Dict, Any

import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter()


# Mini “base de datos” de variantes conocidas (por nombre de archivo)
# Solo se usan identificadores simples en el nombre del archivo FASTA.
KNOWN_VARIANTS = [
    {
        "match_keywords": ["185delag"],
        "gene": "BRCA1",
        "cdna_change": "c.68_69delAG",
        "protein_change": "p.Glu23Valfs*17",
        "clinvar_id": "17661",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17661/",
        "significance": "Pathogenic",
        "associated_cancer": "Cáncer de mama/ovario hereditario",
    },
    {
        "match_keywords": ["5382insc", "c.5266dupc"],
        "gene": "BRCA1",
        "cdna_change": "c.5266dupC",
        "protein_change": "p.Gln1756Profs*74",
        "clinvar_id": "17664",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17664/",
        "significance": "Pathogenic",
        "associated_cancer": "Cáncer de mama/ovario hereditario",
    },
    {
        "match_keywords": ["6174delt", "c.5946delt"],
        "gene": "BRCA2",
        "cdna_change": "c.5946delT",
        "protein_change": "p.Ser1982Argfs*22",
        "clinvar_id": "37949",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/37949/",
        "significance": "Pathogenic",
        "associated_cancer": "Cáncer de mama/ovario hereditario",
    },
    {
        "match_keywords": ["2808_2811delacaa", "2808-2811delacaa"],
        "gene": "BRCA2",
        "cdna_change": "c.2808_2811delACAA",
        "protein_change": "p.Ala938Profs*21",
        "clinvar_id": "23031",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/23031/",
        "significance": "Pathogenic",
        "associated_cancer": "Cáncer de mama/ovario hereditario",
    },
]


def _validate_fasta_filename(kind: str, filename: str) -> None:
    """
    Valida que el archivo tenga un nombre razonable y una extensión esperada.
    Lanza HTTPException con mensaje claro si hay problema.
    """
    if not filename:
        raise HTTPException(
            status_code=400,
            detail=f"Debes adjuntar un archivo FASTA para {kind}.",
        )

    lowered = filename.lower()
    if not lowered.endswith((".fasta", ".fa", ".txt")):
        raise HTTPException(
            status_code=400,
            detail=(
                f"El archivo de {kind} debe estar en formato de texto/FASTA "
                "(.fasta, .fa o .txt). Nombre recibido: " + filename
            ),
        )


def _detect_variants_from_filenames(
    brca1_filename: str,
    brca2_filename: str,
) -> List[Dict[str, Any]]:
    """
    Detecta variantes patogénicas conocidas mirando SOLO el nombre de los archivos.
    Esto está pensado para el MVP de demostración con FASTA simulados.
    """
    variants: List[Dict[str, Any]] = []

    name1 = brca1_filename.lower()
    name2 = brca2_filename.lower()

    for variant in KNOWN_VARIANTS:
        for kw in variant["match_keywords"]:
            if variant["gene"] == "BRCA1" and kw in name1:
                variants.append(
                    {
                        "gene": variant["gene"],
                        "cdna_change": variant["cdna_change"],
                        "protein_change": variant["protein_change"],
                        "clinvar_id": variant["clinvar_id"],
                        "clinvar_url": variant["clinvar_url"],
                        "significance": variant["significance"],
                        "associated_cancer": variant["associated_cancer"],
                        "source_file": brca1_filename,
                    }
                )
                break
            if variant["gene"] == "BRCA2" and kw in name2:
                variants.append(
                    {
                        "gene": variant["gene"],
                        "cdna_change": variant["cdna_change"],
                        "protein_change": variant["protein_change"],
                        "clinvar_id": variant["clinvar_id"],
                        "clinvar_url": variant["clinvar_url"],
                        "significance": variant["significance"],
                        "associated_cancer": variant["associated_cancer"],
                        "source_file": brca2_filename,
                    }
                )
                break

    return variants


@router.post("/run_for_patient")
async def run_analysis_for_patient(
    patient_id: int = Query(..., description="ID del paciente al que se asocia el análisis"),
    brca1_file: UploadFile = File(..., description="Archivo FASTA correspondiente a BRCA1"),
    brca2_file: UploadFile = File(..., description="Archivo FASTA correspondiente a BRCA2"),
    db: Session = Depends(get_db),
):
    """
    Ejecuta un análisis germinal simple para BRCA1/BRCA2:

    - Verifica que el paciente exista.
    - Valida que se hayan enviado ambos archivos y que tengan extensiones adecuadas.
    - Detecta variantes patogénicas conocidas a partir del nombre del archivo
      (pensado para FASTA de prueba con mutaciones específicas).
    - Guarda el resultado completo en la tabla germline_analyses.
    """

    # 1) Verificar que el paciente exista
    patient = (
        db.query(models.Patient)
        .filter(models.Patient.id == patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    # 2) Validar nombres de archivo y extensiones
    _validate_fasta_filename("BRCA1", brca1_file.filename)
    _validate_fasta_filename("BRCA2", brca2_file.filename)

    # 3) Detectar variantes conocidas
    variants = _detect_variants_from_filenames(
        brca1_filename=brca1_file.filename,
        brca2_filename=brca2_file.filename,
    )

    # 4) Construir mensaje resumen
    if variants:
        summary = (
            f"Se detectaron {len(variants)} variantes germinales patogénicas "
            "conocidas en BRCA1/BRCA2."
        )
    else:
        summary = (
            "No se detectaron variantes germinales patogénicas conocidas en los archivos "
            "FASTA analizados. Esto no excluye la presencia de otras variantes no incluidas "
            "en la mini base de datos local de este prototipo."
        )

    # 5) Construir payload de resultado (lo que verá el frontend)
    result_payload: Dict[str, Any] = {
        "patient_id": patient_id,
        "summary": summary,
        "variants": variants,
    }

    # 6) Guardar en la base de datos
    analysis_row = models.GermlineAnalysis(
        patient_id=patient_id,
        description="Análisis germinal BRCA1/BRCA2 (demo por nombre de archivo).",
        summary=summary,
        raw_result=json.dumps(result_payload, ensure_ascii=False),
    )
    db.add(analysis_row)
    db.commit()
    db.refresh(analysis_row)

    # 7) Devolver el resultado incluyendo el ID de análisis
    result_payload["analysis_id"] = analysis_row.id
    return result_payload
