# app/services/analysis.py

from typing import List, Dict
from datetime import datetime

# Aquí podrías importar Biopython si más adelante lo usas
# from Bio import SeqIO

def _read_fasta(path: str) -> str:
    """Lee una secuencia FASTA simple, devolviendo sólo la secuencia."""
    seq = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith(">"):
                continue
            seq.append(line.strip().upper())
    return "".join(seq)


def run_germline_analysis(brca1_path: str, brca2_path: str) -> Dict:
    """
    Analiza las secuencias BRCA1 y BRCA2 y devuelve un dict con:
    - riesgo global
    - lista de mutaciones (falsas/sintéticas por ahora)
    """
    brca1 = _read_fasta(brca1_path)
    brca2 = _read_fasta(brca2_path)

    # Aquí podrías hacer alineamientos reales. Por ahora: lógica demo.
    mutations: List[Dict] = []

    if brca1:
        mutations.append({
            "gene": "BRCA1",
            "hgvs_c": "NM_007294.4:c.5266dupC",
            "significance": "Pathogenic",
            "source": "DemoClinVar",
        })

    if brca2:
        mutations.append({
            "gene": "BRCA2",
            "hgvs_c": "NM_000059.4:c.5946delT",
            "significance": "Pathogenic",
            "source": "DemoClinVar",
        })

    overall_risk = "High" if mutations else "Low"

    return {
        "created_at": datetime.utcnow(),
        "overall_risk": overall_risk,
        "mutations": mutations,
    }
