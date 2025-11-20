# backend/app/api/analysis.py

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app import crud
from app.services.clinvar_client import query_clinvar_hgvs


router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
)


# -----------------------------------------------------------------------------
# Mapa de variantes de DEMO
#
# Importante:
#   - NO analizamos todavía el contenido de los FASTA.
#   - Usamos el NOMBRE DEL ARCHIVO para saber qué mutación simular.
#   - Para cada HGVS consultamos ClinVar en tiempo real.
#
# Los archivos de demo que ya has usado son, por ejemplo:
#   BRCA1_185delAG_patient.fasta
#   BRCA2_2808_2811delACAA_patient.fasta
# -----------------------------------------------------------------------------

VARIANT_MAP = {
    # Paciente con 185delAG en BRCA1
    "BRCA1_185delAG_patient.fasta": [
        {
            "gene": "BRCA1",
            "hgvs_c": "NM_007294.4:c.68_69delAG",
        },
    ],

    # Paciente con 5382insC en BRCA1 (por si luego lo quieres usar)
    "BRCA1_5382insC_patient.fasta": [
        {
            "gene": "BRCA1",
            "hgvs_c": "NM_007294.4:c.5266dupC",
        },
    ],

    # Paciente con 6174delT en BRCA2 (por si luego lo quieres usar)
    "BRCA2_6174delT_patient.fasta": [
        {
            "gene": "BRCA2",
            "hgvs_c": "NM_000059.4:c.5946delT",
        },
    ],

    # Paciente con 2808_2811delACAA en BRCA2
    "BRCA2_2808_2811delACAA_patient.fasta": [
        {
            "gene": "BRCA2",
            "hgvs_c": "NM_000059.3:c.2808_2811delACAA",
        },
    ],
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

async def _build_mutation_record(
    *,
    gene: str,
    source_file: str,
    hgvs_c: str,
) -> dict:
    """
    Consulta ClinVar para un HGVS concreto y devuelve un diccionario estable
    que luego guardamos en la base de datos y devolvemos por la API.
    """

    clinvar_data = query_clinvar_hgvs(hgvs_c)

    # La función query_clinvar_hgvs (que ya probaste en consola) devuelve algo
    # con esta pinta aproximada:
    # {
    #   "clinvar_id": "136539",
    #   "title": "...",
    #   "clinical_significance": "Pathogenic",
    #   "review_status": "...",
    #   "conditions": [...],
    #   "hgvs_c_primary": "NM_007294.4:c.68_69delAG",
    #   "hgvs_c_all": [...],
    #   "hgvs_p_primary": "...",
    #   ...
    # }

    if clinvar_data.get("error"):
        # No lanzamos excepción fuerte, pero lo dejamos registrado en el JSON
        # para que el médico vea qué pasó.
        pass

    mutation = {
        "gene": gene,
        "source_file": source_file,
        "clinvar_id": clinvar_data.get("clinvar_id"),
        "hgvs_c": clinvar_data.get("hgvs_c_primary") or hgvs_c,
        "hgvs_p": clinvar_data.get("hgvs_p_primary"),
        "clinical_significance": clinvar_data.get("clinical_significance"),
        "conditions": clinvar_data.get("conditions", []),
        "raw_json": clinvar_data,  # lo guardamos completo por si acaso
    }

    return mutation


async def _analyze_demo_from_uploads(
    brca1_fasta: UploadFile,
    brca2_fasta: Optional[UploadFile] = None,
) -> dict:
    """
    Implementación DEMO del motor de análisis:

    - NO se lee el contenido del FASTA.
    - Solo se usa el nombre del archivo para buscar en VARIANT_MAP.
    - Para cada HGVS asociado se hace una consulta a ClinVar.
    """

    if brca1_fasta is None:
        raise HTTPException(status_code=400, detail="Se requiere al menos el archivo de BRCA1.")

    mutations: List[dict] = []

    # BRCA1
    brca1_name = brca1_fasta.filename or ""
    brca1_specs = VARIANT_MAP.get(brca1_name)
    if not brca1_specs:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Archivo BRCA1 desconocido para la demo: {brca1_name}. "
                "Usa por ejemplo: BRCA1_185delAG_patient.fasta"
            ),
        )

    for spec in brca1_specs:
        mut = await _build_mutation_record(
            gene=spec["gene"],
            source_file=brca1_name,
            hgvs_c=spec["hgvs_c"],
        )
        mutations.append(mut)

    # BRCA2 (opcional en esta demo)
    if brca2_fasta is not None:
        brca2_name = brca2_fasta.filename or ""
        brca2_specs = VARIANT_MAP.get(brca2_name)
        if not brca2_specs:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Archivo BRCA2 desconocido para la demo: {brca2_name}. "
                    "Usa por ejemplo: BRCA2_2808_2811delACAA_patient.fasta"
                ),
            )

        for spec in brca2_specs:
            mut = await _build_mutation_record(
                gene=spec["gene"],
                source_file=brca2_name,
                hgvs_c=spec["hgvs_c"],
            )
            mutations.append(mut)

    return {"mutations": mutations}


def _save_analysis_to_db(result: dict) -> dict:
    """
    Guarda en la base de datos:
      - Paciente (por ahora 'Paciente demo')
      - Análisis
      - Variantes asociadas

    Devuelve el mismo dict de entrada, añadiendo analysis_id y patient_id.
    """

    db: Session = SessionLocal()
    try:
        # Por ahora usamos un paciente genérico de demostración.
        # Más adelante, cuando tengas frontend, vendrán nombre/documento desde la UI.
        patient = crud.get_or_create_patient(
            db,
            full_name="Paciente demo",
            document_id=None,
        )

        mutations = result.get("mutations", []) or []

        analysis = crud.create_analysis_with_mutations(
            db,
            patient=patient,
            mutations=mutations,
        )

        # Enriquecemos el JSON que devolvemos por la API
        result["analysis_id"] = analysis.id
        result["patient_id"] = patient.id

    finally:
        db.close()

    return result


# -----------------------------------------------------------------------------
# Endpoint público
# -----------------------------------------------------------------------------

@router.post(
    "/run",
    summary="Run Analysis",
    description=(
        "Demo simplificada del módulo de análisis de ONCOATLAS.\n\n"
        "- **No** se analiza todavía el contenido de los archivos FASTA.\n"
        "- Se utiliza el **nombre del archivo** para identificar la mutación "
        "(ver `VARIANT_MAP` en el backend).\n"
        "- Para cada HGVS asociado se consulta **ClinVar** en tiempo real.\n\n"
        "Esta versión es suficiente para demostrar el flujo completo:\n"
        "carga de FASTA → consulta ClinVar → guardado en base de datos → "
        "respuesta JSON lista para el informe clínico."
    ),
)
async def run_analysis(
    brca1_fasta: UploadFile = File(..., description="Archivo FASTA de BRCA1 del paciente"),
    brca2_fasta: Optional[UploadFile] = File(
        None,
        description="Archivo FASTA de BRCA2 del paciente (opcional en esta demo)",
    ),
) -> dict:
    """
    Endpoint principal de análisis.

    1. Ejecuta el análisis DEMO (según nombre de archivo).
    2. Guarda el resultado en la base de datos local (SQLite).
    3. Devuelve el JSON con la lista de mutaciones y los IDs de paciente/análisis.
    """

    # 1) Ejecutar análisis (demo)
    result = await _analyze_demo_from_uploads(brca1_fasta, brca2_fasta)

    # 2) Guardar en BD (paciente demo + análisis + variantes)
    result = _save_analysis_to_db(result)

    # 3) Devolver al cliente (Swagger, frontend, etc.)
    return result


