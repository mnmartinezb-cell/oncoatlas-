from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.analysis_engine import analyze
from app.services.clinvar_client import query_clinvar_hgvs


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    # ------------------------------------------------------------------
    # 1) Rutas básicas
    # ------------------------------------------------------------------
    print_section("1) Rutas del proyecto")

    backend_dir = Path(__file__).resolve().parent          # ...\onco\backend
    project_root = backend_dir.parent                      # ...\onco
    refs_dir = project_root / "refs"

    print(f"backend_dir : {backend_dir}")
    print(f"project_root: {project_root}")
    print(f"refs_dir    : {refs_dir}")

    brca1_ref = refs_dir / "brca1_ref.fasta"
    brca2_ref = refs_dir / "brca2_ref.fasta"

    print_section("2) Verificando archivos de referencia BRCA")

    if brca1_ref.exists():
        print(f"[OK] Existe BRCA1 ref: {brca1_ref}")
    else:
        print(f"[ERROR] No existe BRCA1 ref: {brca1_ref}")

    if brca2_ref.exists():
        print(f"[OK] Existe BRCA2 ref: {brca2_ref}")
    else:
        print(f"[ERROR] No existe BRCA2 ref: {brca2_ref}")

    # ------------------------------------------------------------------
    # 3) Probar motor de análisis (analyze) con ref vs ref
    # ------------------------------------------------------------------
    if brca1_ref.exists() and brca2_ref.exists():
        print_section("3) Probando analyze() con ref vs ref")

        try:
            mutations = analyze(str(brca1_ref), str(brca2_ref))
            print("Resultado de analyze(ref, ref):")
            print(mutations)
            if not mutations:
                print("[OK] No hay mutaciones cuando se comparan ref vs ref (lo esperado).")
            else:
                print("[ADVERTENCIA] Hay mutaciones en ref vs ref. Revisa la lógica de análisis.")
        except Exception as exc:
            print(f"[ERROR] analyze() falló con ref vs ref -> {exc}")
    else:
        print("[INFO] Se omite la prueba de analyze() porque faltan referencias.")

    # ------------------------------------------------------------------
    # 4) Probar integración con ClinVar para varias variantes
    # ------------------------------------------------------------------
    print_section("4) Probando query_clinvar_hgvs() con variantes BRCA reales")

    hgvs_list = [
        "NM_007294.4:c.68_69delAG",      # BRCA1 185delAG
        "NM_007294.4:c.5266dupC",       # BRCA1 5382insC
        "NM_000059.4:c.5946delT",       # BRCA2 6174delT
        "NM_000059.3:c.2808_2811delACAA",  # BRCA2 2808_2811delACAA
    ]

    for hgvs in hgvs_list:
        print(f"\n--- Consultando ClinVar para {hgvs} ---")
        try:
            result: Any = query_clinvar_hgvs(hgvs)
            print(result)
            if result:
                print("clinvar_id           :", result.get("clinvar_id"))
                print("clinical_significance:", result.get("clinical_significance"))
            else:
                print("[ADVERTENCIA] ClinVar devolvió None.")
        except Exception as exc:
            print(f"[ERROR] Fallo al consultar ClinVar para {hgvs} -> {exc}")

    print_section("DIAGNÓSTICO COMPLETADO")


if __name__ == "__main__":
    main()
