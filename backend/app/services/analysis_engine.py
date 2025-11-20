# backend/app/services/analysis_engine.py

"""
Motor de análisis simplificado para Oncoatlas (demo ClinVar online).

Idea:
- Usamos el NOMBRE DEL ARCHIVO FASTA para saber qué mutación contiene.
- Mapa filename -> (GEN, HGVS_c).
- Consultamos ClinVar con ese HGVS_c.
- Devolvemos una lista de dicts con la información combinada.

Esto nos permite probar el flujo completo:
FASTA de paciente -> /analysis/run -> ClinVar en tiempo real,
sin todavía implementar el alineamiento real ni el llamado automático HGVS.
"""

from pathlib import Path
from typing import Any, Dict, List, Union

from app.services.clinvar_client import query_clinvar_hgvs

# Mapa de archivos de prueba -> (GEN, HGVS_c)
VARIANT_MAP: Dict[str, tuple[str, str]] = {
    # BRCA1
    "BRCA1_185delAG_patient.fasta": ("BRCA1", "NM_007294.4:c.68_69delAG"),
    "BRCA1_5382insC_patient.fasta": ("BRCA1", "NM_007294.4:c.5266dupC"),
    # BRCA2
    "BRCA2_6174delT_patient.fasta": ("BRCA2", "NM_000059.4:c.5946delT"),
    "BRCA2_2808_2811delACAA_patient.fasta": ("BRCA2", "NM_000059.3:c.2808_2811delACAA"),
}


def analyze_single_fasta(fasta_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Versión mínima: decide la mutación por el NOMBRE DEL ARCHIVO
    y consulta ClinVar con ese HGVS.

    Si el archivo no está en VARIANT_MAP -> devuelve lista vacía.
    """
    path = Path(fasta_path)
    filename = path.name

    if filename not in VARIANT_MAP:
        # Por ahora, si el archivo no es uno de los 4 de prueba, decimos "sin mutaciones detectadas".
        return []

    gene, hgvs_c = VARIANT_MAP[filename]
    clinvar = query_clinvar_hgvs(hgvs_c)

    result: Dict[str, Any] = {
        "gene": gene,
        "source_file": filename,
        "hgvs_c": hgvs_c,
    }
    # Añadimos los campos que devuelve clinvar_client
    result.update(clinvar)

    return [result]


def analyze(brca1_path: str, brca2_path: str) -> List[Dict[str, Any]]:
    """
    Función "legacy" por si en algún sitio antiguo se sigue llamando analyze(ref1, ref2).

    Para esta demo simplemente llama a analyze_single_fasta en cada archivo
    y concatena las listas.
    """
    results: List[Dict[str, Any]] = []
    results.extend(analyze_single_fasta(brca1_path))
    results.extend(analyze_single_fasta(brca2_path))
    return results
