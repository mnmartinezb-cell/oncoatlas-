"""
make_brca1_5382insC_patient.py

Lee la referencia BRCA1 (mRNA NM_007294.4 o similar) desde
refs/brca1_ref.fasta y genera un FASTA de paciente con la mutación:

    BRCA1 c.5266dupC (5382insC, p.Gln1756Profs*74)

Asume que la numeración cDNA (c.) empieza en el codón de inicio ATG.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # carpeta onco/
REF_PATH = ROOT / "refs" / "brca1_ref.fasta"
OUT_PATH = ROOT / "tests" / "fasta_samples" / "BRCA1_5382insC_patient.fasta"


def read_fasta_seq(path: Path) -> str:
    seq = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith(">"):
                continue
            seq.append(line.upper())
    return "".join(seq)


def write_fasta(path: Path, header: str, seq: str, line_width: int = 60) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(f">{header}\n")
        for i in range(0, len(seq), line_width):
            fh.write(seq[i:i + line_width] + "\n")


def main() -> None:
    if not REF_PATH.exists():
        raise FileNotFoundError(f"No se encontró la referencia: {REF_PATH}")

    ref_seq = read_fasta_seq(REF_PATH)
    print(f"Longitud referencia BRCA1 (mRNA): {len(ref_seq)} bases")

    # 1) Encontrar el codón de inicio ATG (c.1 = A de este ATG)
    start_codon = "ATG"
    start_idx = ref_seq.find(start_codon)
    if start_idx == -1:
        raise ValueError("No se encontró ningún ATG en la referencia BRCA1.")

    print(f"Codón de inicio ATG encontrado en índice 0-based: {start_idx}")
    print(f"Esto corresponde a posición c.1 = índice {start_idx} (A del ATG)")

    # 2) Calcular la posición de c.5266 relativa al ATG
    # c.1    -> ref_seq[start_idx]
    # c.5266 -> ref_seq[start_idx + 5265]
    c_pos = 5266
    idx_c = start_idx + (c_pos - 1)

    motif = ref_seq[idx_c:idx_c + 1]
    print(f"Base en c.{c_pos} en la referencia: {motif!r}")

    if motif != "C":
        raise ValueError(
            f"En la referencia BRCA1, en c.{c_pos} se esperaba 'C' "
            f"para 5382insC (c.5266dupC), pero se encontró {motif!r}. "
            "¿Seguro que el FASTA corresponde a NM_007294.4 mRNA canónico?"
        )

    # 3) Aplicar la duplicación: duplicar la C en c.5266
    # ref: ...C...
    # mutado: ...CC...
    patient_seq = ref_seq[:idx_c + 1] + "C" + ref_seq[idx_c + 1:]

    print(f"Longitud paciente (con 5382insC): {len(patient_seq)} bases")

    header = (
        "BRCA1 NM_007294.4 c.5266dupC (5382insC, p.Gln1756Profs*74) "
        "synthetic patient sequence"
    )
    write_fasta(OUT_PATH, header, patient_seq)

    print(f"✔ FASTA generado: {OUT_PATH}")


if __name__ == "__main__":
    main()
