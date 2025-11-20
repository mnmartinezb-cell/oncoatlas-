"""
make_brca2_6174delT_patient.py

Lee la referencia BRCA2 (mRNA NM_000059.4 o similar) desde
refs/brca2_ref.fasta y genera un FASTA de paciente con la mutación:

    BRCA2 c.5946delT (6174delT, p.Ser1982Argfs*22)

Asume que la numeración cDNA (c.) empieza en el codón de inicio ATG.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # carpeta onco/
REF_PATH = ROOT / "refs" / "brca2_ref.fasta"
OUT_PATH = ROOT / "tests" / "fasta_samples" / "BRCA2_6174delT_patient.fasta"


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

    # 2) Calcular la posición de c.5946 relativa al ATG
    # c.1    -> ref_seq[start_idx]
    # c.5946 -> ref_seq[start_idx + 5945]
    c_pos = 5946

    idx_c = start_idx + (c_pos - 1)

    motif = ref_seq[idx_c:idx_c + 1]
    print(f"Base en c.{c_pos} en la referencia: {motif!r}")

    if motif != "T":
        raise ValueError(
            f"En la referencia BRCA2, en c.{c_pos} se esperaba 'T' "
            f"para 6174delT, pero se encontró {motif!r}. "
            "¿Seguro que el FASTA corresponde a NM_000059.4 mRNA canónico?"
        )

    # 3) Aplicar la deleción: eliminar la base c.5946 (T)
    patient_seq = ref_seq[:idx_c] + ref_seq[idx_c + 1:]

    print(f"Longitud paciente (con 6174delT): {len(patient_seq)} bases")

    header = (
        "BRCA2 NM_000059.4 c.5946delT (p.Ser1982Argfs*22) "
        "synthetic patient sequence"
    )
    write_fasta(OUT_PATH, header, patient_seq)

    print(f"✔ FASTA generado: {OUT_PATH}")


if __name__ == "__main__":
    main()
