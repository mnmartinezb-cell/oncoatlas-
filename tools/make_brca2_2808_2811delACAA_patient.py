"""
make_brca2_2808_2811delACAA_patient.py

Lee la referencia BRCA2 (mRNA NM_000059.4 o similar) desde
refs/brca2_ref.fasta y genera un FASTA de paciente con la mutación:

    BRCA2 c.2808_2811delACAA (p.Ala938Profs*21)

Asume que la numeración cDNA (c.) empieza en el codón de inicio ATG.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # carpeta onco/
REF_PATH = ROOT / "refs" / "brca2_ref.fasta"
OUT_PATH = ROOT / "tests" / "fasta_samples" / "BRCA2_2808_2811delACAA_patient.fasta"


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
    print(f"Longitud referencia BRCA2 (mRNA): {len(ref_seq)} bases")

    # 1) Encontrar el codón de inicio ATG (c.1 = A de este ATG)
    start_codon = "ATG"
    start_idx = ref_seq.find(start_codon)
    if start_idx == -1:
        raise ValueError("No se encontró ningún ATG en la referencia BRCA2.")

    print(f"Codón de inicio ATG encontrado en índice 0-based: {start_idx}")
    print(f"Esto corresponde a posición c.1 = índice {start_idx} (A del ATG)")

    # 2) Calcular la región c.2808_2811 relativa al ATG
    # c.1        -> ref_seq[start_idx]
    # c.2808     -> ref_seq[start_idx + 2807]
    # c.2811     -> ref_seq[start_idx + 2810]
    c_start = 2808
    c_end = 2811

    idx_start = start_idx + (c_start - 1)
    idx_end_exclusive = start_idx + c_end  # porque c_end es inclusivo

    motif = ref_seq[idx_start:idx_end_exclusive]
    print(f"Bases en c.{c_start}_{c_end} en la referencia: {motif!r}")

    expected = "ACAA"
    if motif != expected:
        raise ValueError(
            f"En la referencia BRCA2, en c.{c_start}_{c_end} se esperaba "
            f"'{expected}' para c.2808_2811delACAA, pero se encontró {motif!r}. "
            "¿Seguro que el FASTA corresponde a NM_000059.4 mRNA canónico?"
        )

    # 3) Aplicar la deleción: eliminar ACAA (4 nt)
    patient_seq = ref_seq[:idx_start] + ref_seq[idx_end_exclusive:]

    print(f"Longitud paciente (con c.2808_2811delACAA): {len(patient_seq)} bases")

    header = (
        "BRCA2 NM_000059.4 c.2808_2811delACAA (p.Ala938Profs*21) "
        "synthetic patient sequence"
    )
    write_fasta(OUT_PATH, header, patient_seq)

    print(f"✔ FASTA generado: {OUT_PATH}")


if __name__ == "__main__":
    main()
