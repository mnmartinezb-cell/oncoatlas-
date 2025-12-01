# backend/app/services/analysis_service.py

from pathlib import Path
from typing import Any, Dict, List, Tuple


# -------------------------------------------------------------------
# Mini "base de datos" interna de variantes BRCA1/BRCA2 bien conocidas
# -------------------------------------------------------------------
# Esto sirve para que tus FASTA sintéticos (185delAG, 5382insC,
# 2808_2811delACAA, 6174delT) se anoten automáticamente con ClinVar.

MINI_CLINVAR_DB: List[Dict[str, Any]] = [
    {
        "gene": "BRCA1",
        "cdna_change": "c.68_69delAG",
        "protein_change": "p.Glu23Valfs*17",
        "legacy_name": "185delAG",
        "clinvar_id": "17662",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17662/",
        "classification": "Pathogenic",
        "variant_type": "frameshift",
    },
    {
        "gene": "BRCA1",
        "cdna_change": "c.5266dupC",
        "protein_change": "p.Gln1756Profs*74",
        "legacy_name": "5382insC",
        "clinvar_id": "17677",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17677/",
        "classification": "Pathogenic",
        "variant_type": "frameshift",
    },
    {
        "gene": "BRCA2",
        "cdna_change": "c.2808_2811delACAA",
        "protein_change": "p.Ala938Profs*21",
        "legacy_name": "3036delACAA",
        "clinvar_id": "9322",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/9322/",
        "classification": "Pathogenic",
        "variant_type": "frameshift",
    },
    {
        "gene": "BRCA2",
        "cdna_change": "c.5946delT",
        "protein_change": "p.Ser1982Argfs*22",
        "legacy_name": "6174delT",
        "clinvar_id": "9325",
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/9325/",
        "classification": "Pathogenic",
        "variant_type": "frameshift",
    },
]


# -----------------------
# Funciones auxiliares
# -----------------------

def _load_fasta(path: Path | str) -> Tuple[str, str]:
    """
    Lee un FASTA sencillo y devuelve (cabecera, secuencia).
    """
    p = Path(path)
    header = ""
    seq_lines: List[str] = []

    with p.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if not header:
                    header = line[1:].strip()
                continue
            seq_lines.append(line.upper())

    sequence = "".join(seq_lines)
    return header, sequence


def _detect_known_pathogenic_variants(header: str, gene: str) -> List[Dict[str, Any]]:
    """
    Busca en la CABECERA del FASTA nombres de variantes fundadoras conocidas:
    - 185delAG
    - 5382insC
    - 2808_2811delACAA
    - 6174delT

    y devuelve una lista de variantes ya anotadas con su ClinVar.
    """
    header_lower = header.lower()
    results: List[Dict[str, Any]] = []

    for var in MINI_CLINVAR_DB:
        if var["gene"] != gene:
            continue

        # Palabras clave que pueden aparecer en la cabecera.
        candidates = {
            var["cdna_change"].lower(),
            var["legacy_name"].lower(),
        }

        if any(token in header_lower for token in candidates):
            results.append(
                {
                    "gene": var["gene"],
                    "cdna_change": var["cdna_change"],
                    "protein_change": var["protein_change"],
                    "variant_type": var["variant_type"],
                    "classification": var["classification"],
                    "clinvar_id": var["clinvar_id"],
                    "clinvar_url": var["clinvar_url"],
                    "notes": (
                        f"Variante fundadora conocida ({var['legacy_name']}). "
                        "Anotación basada en ClinVar (uso didáctico)."
                    ),
                }
            )

    return results


def _detect_simple_snvs(
    gene: str,
    patient_seq: str,
    ref_seq: str,
    max_variants: int = 50,
) -> List[Dict[str, Any]]:
    """
    Detección MUY simple de SNVs por comparación base a base.
    Se usa solo como contenido de demostración cuando no se ha
    reconocido ninguna variante fundadora en la cabecera.
    """
    length = min(len(patient_seq), len(ref_seq))
    variants: List[Dict[str, Any]] = []

    for i in range(length):
        if patient_seq[i] != ref_seq[i]:
            pos = i + 1  # posiciones 1-based
            variants.append(
                {
                    "gene": gene,
                    "cdna_change": f"c.{pos}{ref_seq[i]}>{patient_seq[i]}",
                    "protein_change": "NA",
                    "variant_type": "SNV",
                    "classification": "VUS (demostración)",
                    "clinvar_id": None,
                    "clinvar_url": None,
                    "notes": (
                        "Variante detectada por comparación simple en Oncoatlas; "
                        "no corresponde a una anotación real de ClinVar."
                    ),
                }
            )
            if len(variants) >= max_variants:
                break

    return variants


# -----------------------------------------------
# Función principal que usará el router analyses
# -----------------------------------------------

def run_germline_analysis(
    brca1_fasta_path: str,
    brca2_fasta_path: str,
) -> Dict[str, Any]:
    """
    Función principal de análisis germinal BRCA1/BRCA2 para Oncoatlas.

    - Lee los FASTA del paciente.
    - Compara con las referencias locales (backend/refs/brca1_ref.fasta,
      backend/refs/brca2_ref.fasta).
    - Intenta reconocer variantes fundadoras conocidas a partir de la
      CABECERA del FASTA (185delAG, 5382insC, 2808_2811delACAA, 6174delT).
    - Si no hay fundadoras, genera una lista corta de SNVs de demostración.
    """
    # FASTA del paciente
    brca1_header, brca1_seq = _load_fasta(brca1_fasta_path)
    brca2_header, brca2_seq = _load_fasta(brca2_fasta_path)

    # Referencias locales (dentro de backend/refs)
    base_dir = Path(__file__).resolve().parents[2]  # .../backend
    refs_dir = base_dir / "refs"

    brca1_ref_header, brca1_ref_seq = _load_fasta(refs_dir / "brca1_ref.fasta")
    brca2_ref_header, brca2_ref_seq = _load_fasta(refs_dir / "brca2_ref.fasta")

    # 1) Variantes fundadoras conocidas
    brca1_founders = _detect_known_pathogenic_variants(brca1_header, "BRCA1")
    brca2_founders = _detect_known_pathogenic_variants(brca2_header, "BRCA2")

    # 2) Si no hay fundadoras para un gen, añadimos SNVs simples como demo
    if brca1_founders:
        brca1_snvs: List[Dict[str, Any]] = []
