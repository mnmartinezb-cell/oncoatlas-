from typing import Any, Dict, List, Optional

# Tipo para un registro de variante
VariantRecord = Dict[str, Any]

# Mini base de datos local de variantes germinales BRCA1/BRCA2
VARIANTS: List[VariantRecord] = [
    {
        "gene": "BRCA1",
        "hgvs_c": "c.68_69delAG",  # 185delAG
        "protein_change": "p.Glu23Valfs*17",
        "aliases": ["c.185delAG", "185delAG"],
        "cancer_risk": (
            "Asociada a síndrome de cáncer de mama y ovario hereditario; "
            "mutación fundadora frecuente en poblaciones Ashkenazí."
        ),
        "clinical_significance": "Pathogenic",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17662/",
    },
    {
        "gene": "BRCA1",
        "hgvs_c": "c.5266dupC",  # 5382insC
        "protein_change": "p.Gln1756Profs*74",
        "aliases": ["5382insC", "c.5266_5267insC"],
        "cancer_risk": (
            "Asociada a síndrome de cáncer de mama y ovario hereditario; "
            "mutación fundadora en varias poblaciones europeas."
        ),
        "clinical_significance": "Pathogenic",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/VCV000017677/",
    },
    {
        "gene": "BRCA2",
        "hgvs_c": "c.2808_2811delACAA",
        "protein_change": "p.Ala938Profs*21",
        "aliases": ["c.2808_2811del", "3036delACAA"],
        "cancer_risk": (
            "Asociada a síndrome de cáncer de mama y ovario hereditario; "
            "reportada en múltiples familias con cáncer hereditario."
        ),
        "clinical_significance": "Pathogenic",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/9322/",
    },
    {
        "gene": "BRCA2",
        "hgvs_c": "c.5946delT",  # 6174delT
        "protein_change": "p.Ser1982Argfs*22",
        "aliases": ["c.5946del", "6174delT"],
        "cancer_risk": (
            "Mutación fundadora bien descrita en BRCA2; asociada a alto riesgo "
            "de cáncer de mama y ovario hereditario."
        ),
        "clinical_significance": "Pathogenic",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/9325/",
    },
]

# Alias para código viejo
LOCAL_GERMLINE_VARIANTS: List[VariantRecord] = VARIANTS


def _normalise(code: str) -> str:
    """Normaliza un nombre de variante para compararlo sin detalles de formato."""
    code = code.strip()
    if code.startswith("c."):
        code = code[2:]
    code = code.replace(" ", "")
    return code


def get_variant_info(gene: str, variant_code: str) -> Optional[VariantRecord]:
    """
    Devuelve la información de la variante (o None si no está en la mini BD).
    Se intenta casar tanto por hgvs_c como por los alias definidos.
    """
    gene = gene.strip().upper()
    norm_query = _normalise(variant_code)

    for record in VARIANTS:
        if record["gene"].upper() != gene:
            continue

        # Comparación directa
        if variant_code == record["hgvs_c"]:
            return record

        # Comparación normalizada
        if norm_query == _normalise(record["hgvs_c"]):
            return record

        # Alias
        for alias in record.get("aliases", []):
            if variant_code == alias or norm_query == _normalise(alias):
                return record

    return None

