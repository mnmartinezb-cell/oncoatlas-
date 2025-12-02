# backend/app/services/analysis_service.py

"""
Servicio de análisis germinal BRCA1/BRCA2 para Oncoatlas.

- NO usa Biopython.
- Lee el texto de los FASTA de BRCA1 y BRCA2 (ya cargados por FastAPI).
- Busca mutaciones de interés conocidas en esos archivos.
- Devuelve un diccionario con:
    {
      "variants": [ { ..BRCA1.. }, { ..BRCA2.. } ],
      "summary": "..."
    }
  que es exactamente lo que usan los endpoints /analysis/run y /analysis/run_for_patient.
"""

from typing import Dict, Any, List, Optional


# Mini “base de datos” local de variantes conocidas
KNOWN_VARIANTS: Dict[str, Dict[str, Dict[str, str]]] = {
    "BRCA1": {
        "c.68_69delAG": {
            "gene": "BRCA1",
            "hgvs_c": "c.68_69delAG",
            "protein_change": "p.Glu23Valfs*17",
            "clinical_significance": "Pathogenic",
            "cancer_risk": (
                "Asociada a síndrome de cáncer de mama y ovario hereditario; "
                "mutación fundadora frecuente en poblaciones Ashkenazí."
            ),
            "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17662/",
        }
    },
    "BRCA2": {
        "c.2808_2811delACAA": {
            "gene": "BRCA2",
            "hgvs_c": "c.2808_2811delACAA",
            "protein_change": "p.Ala938Profs*21",
            "clinical_significance": "Pathogenic",
            "cancer_risk": (
                "Asociada a síndrome de cáncer de mama y ovario hereditario; "
                "reportada en múltiples familias con cáncer hereditario."
            ),
            "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/9322/",
        }
    },
}


def _detect_known_variant(gene: str, fasta_text: str) -> Optional[Dict[str, Any]]:
    """
    Detecta si en el FASTA aparece alguna de las variantes conocidas
    de nuestra mini base de datos.

    Para mantenerlo sencillo, buscamos cadenas clave (por ejemplo
    'c.68_69delAG' o '2808_2811delACAA') en TODO el texto del FASTA
    (encabezado + secuencia). Así funciona aunque el nombre esté solo
    en la línea de cabecera.
    """
    gene_db = KNOWN_VARIANTS.get(gene, {})

    for hgvs_c, info in gene_db.items():
        # Buscamos tanto el hgvs completo como una parte típica del nombre
        short_token = hgvs_c.replace("c.", "")
        if hgvs_c in fasta_text or short_token in fasta_text:
            # Devolvemos el dict completo marcándolo como variante conocida
            variant = {
                "gene": info["gene"],
                "hgvs_c": info["hgvs_c"],
                "protein_change": info["protein_change"],
                "known_variant": True,
                "clinical_significance": info["clinical_significance"],
                "cancer_risk": info["cancer_risk"],
                "clinvar_url": info["clinvar_url"],
            }
            return variant

    # Si no encontramos nada: devolvemos None y lo manejamos fuera
    return None


def _build_negative_result(gene: str) -> Dict[str, Any]:
    """
    Construye un resultado cuando no hay variante patogénica conocida.
    """
    return {
        "gene": gene,
        "hgvs_c": "",
        "protein_change": "",
        "known_variant": False,
        "clinical_significance": "No pathogenic variant detected",
        "cancer_risk": (
            "En este análisis básico no se identificaron variantes "
            "patogénicas de interés para este gen."
        ),
        "clinvar_url": "",
    }


def _build_summary(brca1_result: Dict[str, Any],
                   brca2_result: Dict[str, Any]) -> str:
    """
    Genera un texto resumen a partir de los resultados de BRCA1 y BRCA2.
    Reproduce literalmente el texto para las variantes patogénicas conocidas.
    """
    parts: List[str] = []

    # BRCA1
    if brca1_result.get("known_variant"):
        parts.append(
            f"BRCA1 {brca1_result['hgvs_c']}: "
            f"{brca1_result['clinical_significance']}. "
            f"{brca1_result['cancer_risk']}"
        )
    else:
        parts.append(
            "BRCA1: en este análisis básico no se identificaron variantes "
            "patogénicas de interés."
        )

    # BRCA2
    if brca2_result.get("known_variant"):
        parts.append(
            f"BRCA2 {brca2_result['hgvs_c']}: "
            f"{brca2_result['clinical_significance']}. "
            f"{brca2_result['cancer_risk']}"
        )
    else:
        parts.append(
            "BRCA2: en este análisis básico no se identificaron variantes "
            "patogénicas de interés."
        )

    return " ".join(parts)


# --------- FUNCIÓN PRINCIPAL QUE USA EL BACKEND ---------


async def analyse_brca1_brca2(brca1_text: str, brca2_text: str) -> Dict[str, Any]:
    """
    Analiza los archivos FASTA de BRCA1 y BRCA2 de un paciente:

    - Busca variantes patogénicas conocidas (mini “base de datos” local).
    - Si no encuentra, devuelve un resultado negativo para ese gen.
    - Devuelve un diccionario con lista de variantes y un resumen.

    Este `async` se puede usar con `await` desde los endpoints.
    (No hace operaciones I/O, pero FastAPI funciona igual de bien con async.)
    """

    # Detectamos variantes para cada gen
    brca1_variant = _detect_known_variant("BRCA1", brca1_text)
    brca2_variant = _detect_known_variant("BRCA2", brca2_text)

    if brca1_variant is None:
        brca1_variant = _build_negative_result("BRCA1")

    if brca2_variant is None:
        brca2_variant = _build_negative_result("BRCA2")

    variants: List[Dict[str, Any]] = [brca1_variant, brca2_variant]
    summary = _build_summary(brca1_variant, brca2_variant)

    return {
        "variants": variants,
        "summary": summary,
    }
