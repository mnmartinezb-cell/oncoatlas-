# backend/app/routers/analyses.py

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List
import hashlib
import io
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.local_germline_db import LOCAL_GERMLINE_VARIANTS


router = APIRouter(tags=["analyses"])

# --------------------------------------------------------------------
# Rutas de referencia BRCA1/BRCA2
# --------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app
REF_DIR = BASE_DIR.parent / "refs"                 # backend/refs

BRCA1_REF_PATH = REF_DIR / "BRCA1_ref.fasta"
BRCA2_REF_PATH = REF_DIR / "BRCA2_ref.fasta"


def _read_fasta_file(path: Path) -> tuple[str, str]:
    """
    Lee un archivo FASTA sencillo (una sola secuencia) y devuelve (header, sequence).
    """
    if not path.exists():
        raise RuntimeError(f"No se encontró el archivo de referencia: {path}")

    header = ""
    seq_parts: List[str] = []

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                header = line[1:]
            else:
                seq_parts.append(line.upper())

    return header, "".join(seq_parts)


@lru_cache(maxsize=1)
def load_reference_sequences() -> Dict[str, Dict[str, str]]:
    """
    Carga y cachea las secuencias de referencia BRCA1 y BRCA2.
    """
    brca1_header, brca1_seq = _read_fasta_file(BRCA1_REF_PATH)
    brca2_header, brca2_seq = _read_fasta_file(BRCA2_REF_PATH)

    return {
        "BRCA1": {"header": brca1_header, "seq": brca1_seq},
        "BRCA2": {"header": brca2_header, "seq": brca2_seq},
    }


async def read_uploaded_fasta(upload: UploadFile) -> tuple[str, str]:
    """
    Lee un UploadFile FASTA y devuelve (header, sequence).
    """
    content = await upload.read()
    text = content.decode("utf-8", errors="ignore")

    header = ""
    seq_parts: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            header = line[1:]
        else:
            seq_parts.append(line.upper())

    return header, "".join(seq_parts)


# --------------------------------------------------------------------
# Algoritmo simple de SNV
# --------------------------------------------------------------------


def find_snvs_simple(
    ref_seq: str,
    sample_seq: str,
    gene: str,
    max_snvs_preview: int = 500,
) -> tuple[List[Dict[str, Any]], int]:
    """
    Compara dos secuencias (ref vs paciente) y detecta SNVs simples (cambio de base).

    Devuelve:
      - lista de SNV (máximo max_snvs_preview para vista previa)
      - número total de diferencias en toda la longitud comparada
    """
    snvs_preview: List[Dict[str, Any]] = []

    n = min(len(ref_seq), len(sample_seq))
    total_diffs = 0

    for i in range(n):
        r = ref_seq[i]
        s = sample_seq[i]
        if r != s:
            total_diffs += 1
            if len(snvs_preview) < max_snvs_preview:
                snvs_preview.append(
                    {
                        "gene": gene,
                        "position": i + 1,  # 1-based
                        "ref": r,
                        "alt": s,
                        "type": "SNV",
                    }
                )

    # Si hay cola en una de las secuencias, la contamos como diferencias adicionales
    if len(ref_seq) != len(sample_seq):
        total_diffs += abs(len(ref_seq) - len(sample_seq))

    return snvs_preview, total_diffs


# --------------------------------------------------------------------
# Mini BD local: detección por MD5 y longitud
# --------------------------------------------------------------------


def find_known_pathogenic_variants_from_sequence(seq: str, gene: str) -> List[Dict[str, Any]]:
    """
    Dada una secuencia FASTA de paciente y el gen (BRCA1 o BRCA2),
    devuelve la lista de variantes patogénicas reconocidas en la
    mini BD local (LOCAL_GERMLINE_VARIANTS).

    Se basa en:
      - longitud de la secuencia
      - hash MD5 de la secuencia

    Esto está pensado para las 4 secuencias de prueba que usas en ONCOATLAS:
      BRCA1_185delAG, BRCA1_5382insC,
      BRCA2_2808_2811delACAA, BRCA2_6174delT.
    """
    if not seq:
        return []

    seq = seq.upper()
    md5 = hashlib.md5(seq.encode("ascii")).hexdigest()
    length = len(seq)

    hits: List[Dict[str, Any]] = []

    for v in LOCAL_GERMLINE_VARIANTS:
        if v["gene"] != gene:
            continue
        if v["fasta_md5"] == md5 and v["fasta_length"] == length:
            hits.append(
                {
                    "gene": v["gene"],
                    "code": v["code"],
                    "short_name": v["short_name"],
                    "hgvs_c": v["hgvs_c"],
                    "hgvs_p": v["hgvs_p"],
                    "variant_type": v["variant_type"],
                    "pathogenicity": v["pathogenicity"],
                    "main_cancers": v["main_cancers"],
                    "clinvar_url": v["clinvar_url"],
                }
            )

    return hits


# --------------------------------------------------------------------
# Utilidades de BD
# --------------------------------------------------------------------


def get_patient_or_404(db: Session, patient_id: int) -> models.Patient:
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")
    return patient


def build_text_summary(details: Dict[str, Any]) -> str:
    """
    Construye un texto de resumen legible a partir de los detalles del análisis.
    """
    brca1 = details.get("brca1") or {}
    brca2 = details.get("brca2") or {}

    snv_brca1 = int(brca1.get("snv_count") or 0)
    snv_brca2 = int(brca2.get("snv_count") or 0)
    total_snvs = snv_brca1 + snv_brca2

    pv = details.get("pathogenic_variants") or {}
    pv_brca1 = pv.get("BRCA1") or []
    pv_brca2 = pv.get("BRCA2") or []
    all_hits = pv_brca1 + pv_brca2

    partes: List[str] = []

    partes.append(
        f"Se detectaron {total_snvs} diferencias simples (SNV) entre las secuencias del paciente "
        f"y las referencias internas (BRCA1: {snv_brca1}; BRCA2: {snv_brca2})."
    )

    if all_hits:
        frases = []
        for hit in all_hits:
            cancers = ", ".join(hit.get("main_cancers") or [])
            label = f"{hit.get('gene', '')} {hit.get('short_name', '')} ({hit.get('hgvs_c', '')})"
            patog = hit.get("pathogenicity", "Pathogenic")
            if cancers:
                frases.append(f"{label}, {patog}, asociado a {cancers}.")
            else:
                frases.append(f"{label}, {patog}.")
        partes.append(
            " En la mini base de datos germinal local de Oncoatlas se reconocieron variantes "
            "con anotación clínica: " + " ".join(frases)
        )
    else:
        partes.append(
            " En la mini base de datos germinal local de Oncoatlas no se identificaron variantes "
            "con anotación clínica para estas secuencias."
        )

    partes.append(
        " Este resultado es de uso académico/didáctico y debe confirmarse con pruebas de laboratorio "
        "y una base de datos genética completa antes de usarse en clínica."
    )

    return "".join(partes)


def create_analysis_record(
    db: Session,
    patient_id: int,
    status: str,
    summary: str,
    details_dict: Dict[str, Any],
) -> models.Analysis:
    """
    Crea y guarda un registro de Analysis en la base de datos.
    details se almacena como JSON string.
    """
    analysis = models.Analysis(
        patient_id=patient_id,
        status=status,
        summary=summary,
        details=json.dumps(details_dict, ensure_ascii=False),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


# --------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------


@router.get(
    "/patients/{patient_id}/analyses",
    response_model=list[schemas.Analysis],
)
def list_analyses_for_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    """
    Lista todos los análisis registrados para un paciente.
    """
    get_patient_or_404(db, patient_id)
    analyses = (
        db.query(models.Analysis)
        .filter(models.Analysis.patient_id == patient_id)
        .order_by(models.Analysis.created_at.desc())
        .all()
    )
    return analyses


@router.get(
    "/analyses/{analysis_id}",
    response_model=schemas.Analysis,
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un análisis concreto por su ID (sin filtrar por paciente).
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    return analysis


@router.post(
    "/patients/{patient_id}/analyses/run-germline",
    response_model=schemas.Analysis,
    status_code=201,
)
async def run_germline_analysis(
    patient_id: int,
    brca1_fasta: UploadFile = File(...),
    brca2_fasta: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ejecuta el análisis germinal simplificado para BRCA1/BRCA2:

    - Usa las secuencias de referencia locales (BRCA1_ref.fasta, BRCA2_ref.fasta).
    - Compara con las secuencias FASTA cargadas del paciente.
    - Calcula SNVs simplescomo medida de diferencia.
    - Detecta mutaciones patogénicas concretas si la secuencia coincide
      con alguna de las 4 cadenas de prueba de la mini BD local.
    """
    patient = get_patient_or_404(db, patient_id)
    refs = load_reference_sequences()

    # Leer FASTA del paciente
    brca1_header_p, brca1_seq_p = await read_uploaded_fasta(brca1_fasta)
    brca2_header_p, brca2_seq_p = await read_uploaded_fasta(brca2_fasta)

    if not brca1_seq_p or not brca2_seq_p:
        raise HTTPException(
            status_code=400,
            detail="Los archivos FASTA de BRCA1 y BRCA2 del paciente no pueden estar vacíos.",
        )

    # Referencias
    brca1_ref_seq = refs["BRCA1"]["seq"]
    brca2_ref_seq = refs["BRCA2"]["seq"]
    brca1_ref_header = refs["BRCA1"]["header"]
    brca2_ref_header = refs["BRCA2"]["header"]

    # SNVs BRCA1 y BRCA2
    brca1_snvs_preview, brca1_total_snvs = find_snvs_simple(
        brca1_ref_seq,
        brca1_seq_p,
        gene="BRCA1",
        max_snvs_preview=500,
    )
    brca2_snvs_preview, brca2_total_snvs = find_snvs_simple(
        brca2_ref_seq,
        brca2_seq_p,
        gene="BRCA2",
        max_snvs_preview=500,
    )

    # Mutaciones patogénicas conocidas (mini BD local)
    pathogenic_brca1 = find_known_pathogenic_variants_from_sequence(brca1_seq_p, "BRCA1")
    pathogenic_brca2 = find_known_pathogenic_variants_from_sequence(brca2_seq_p, "BRCA2")

    details_dict: Dict[str, Any] = {
        "patient_id": patient.id,
        "generated_at": datetime.utcnow().isoformat(),
        "rules_source": [
            "Alineamiento simple posición a posición BRCA1/BRCA2 (SNV).",
            "Mini base de datos local de variantes germinales patogénicas (MD5 + longitud).",
        ],
        "brca1": {
            "ref_header": brca1_ref_header,
            "ref_length": len(brca1_ref_seq),
            "sample_header": brca1_header_p or brca1_fasta.filename or "",
            "sample_length": len(brca1_seq_p),
            "snv_count": brca1_total_snvs,
            "snvs": brca1_snvs_preview,
        },
        "brca2": {
            "ref_header": brca2_ref_header,
            "ref_length": len(brca2_ref_seq),
            "sample_header": brca2_header_p or brca2_fasta.filename or "",
            "sample_length": len(brca2_seq_p),
            "snv_count": brca2_total_snvs,
            "snvs": brca2_snvs_preview,
        },
        "pathogenic_variants": {
            "BRCA1": pathogenic_brca1,
            "BRCA2": pathogenic_brca2,
        },
    }

    summary_text = build_text_summary(details_dict)

    analysis = create_analysis_record(
        db=db,
        patient_id=patient.id,
        status="completed",
        summary=summary_text,
        details_dict=details_dict,
    )

    return analysis

