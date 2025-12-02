from pathlib import Path
from typing import Dict, Any, List
import json

from fpdf import FPDF


# Carpeta donde se guardarán los PDFs: backend/storage
BASE_DIR = Path(__file__).resolve().parent       # backend/app
STORAGE_DIR = BASE_DIR.parent / "storage"        # backend/storage
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AnalysisReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Informe de análisis germinal BRCA1/BRCA2", ln=1, align="C")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _build_analysis_dict(variants_json: str, summary: str) -> Dict[str, Any]:
    """
    Reconstruye un diccionario estándar de análisis a partir de lo que hay en la BD.
    Maneja tanto el caso en que variants_json es una lista en JSON como
    un dict {"variants": [...]}.
    """
    raw: Any = []
    if variants_json:
        try:
            raw = json.loads(variants_json)
        except json.JSONDecodeError:
            raw = []

    variants: List[Dict[str, Any]]
    if isinstance(raw, list):
        variants = raw
    elif isinstance(raw, dict):
        v = raw.get("variants", [])
        variants = v if isinstance(v, list) else []
    else:
        variants = []

    return {
        "variants": variants,
        "summary": summary or "",
    }


def generate_analysis_report_pdf_file(
    patient_id: str,
    analysis_id: int,
    variants_json: str,
    summary: str,
) -> Path:
    """
    Genera el PDF en disco y devuelve la ruta al archivo.
    """
    data = _build_analysis_dict(variants_json, summary)

    pdf = AnalysisReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Datos básicos
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Paciente / ID interno: {patient_id}", ln=1)
    pdf.cell(0, 8, f"ID de análisis: {analysis_id}", ln=1)
    pdf.ln(4)

    # Resumen
    if data["summary"]:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Resumen del resultado:", ln=1)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, data["summary"])
        pdf.ln(4)

    # Variantes
    variants = data["variants"]
    if variants:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Variantes detectadas:", ln=1)

        for v in variants:
            gene = v.get("gene", "")
            hgvs_c = v.get("hgvs_c", "")
            protein = v.get("protein_change", "")
            clin_sig = v.get("clinical_significance", "")
            risk = v.get("cancer_risk", "")
            clinvar_url = v.get("clinvar_url", "")

            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 6, f"{gene} {hgvs_c}", ln=1)

            pdf.set_font("Arial", "", 10)
            if protein:
                pdf.cell(0, 5, f"Proteína: {protein}", ln=1)
            if clin_sig:
                pdf.cell(0, 5, f"Clasificación: {clin_sig}", ln=1)
            if risk:
                pdf.multi_cell(0, 5, f"Riesgo asociado: {risk}")
            if clinvar_url:
                pdf.multi_cell(0, 5, f"ClinVar: {clinvar_url}")
            pdf.ln(3)

    filename = f"analysis_{patient_id}_{analysis_id}.pdf"
    pdf_path = STORAGE_DIR / filename
    pdf.output(str(pdf_path))

    return pdf_path
