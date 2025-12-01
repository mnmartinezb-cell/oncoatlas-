# backend/app/routers/reports.py

from typing import Any, Dict, List
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from app.database import get_db
from app import models


router = APIRouter(
    prefix="/patients",
    tags=["reports"],
)


def _safe_load_details(details_value: Any) -> Dict[str, Any]:
    """
    Devuelve un dict seguro a partir de analysis.details, que puede venir como
    dict, string JSON o None.
    """
    if details_value is None:
        return {}
    if isinstance(details_value, dict):
        return details_value
    if isinstance(details_value, str):
        try:
            return json.loads(details_value)
        except json.JSONDecodeError:
            return {}
    return {}


def _wrap_text(text: str, max_chars: int = 100) -> List[str]:
    """
    Parte un texto largo en líneas de longitud máxima max_chars.
    """
    if not text:
        return [""]
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    length = 0
    for w in words:
        if length + len(w) + (1 if current else 0) > max_chars:
            lines.append(" ".join(current))
            current = [w]
            length = len(w)
        else:
            current.append(w)
            length += len(w) + (1 if current else 0)
    if current:
        lines.append(" ".join(current))
    return lines


@router.get("/{patient_id}/analyses/{analysis_id}/report-pdf")
def generate_analysis_report_pdf(
    patient_id: int,
    analysis_id: int,
    db: Session = Depends(get_db),
):
    """
    Genera un informe PDF clínico para un análisis germinal BRCA1/BRCA2,
    incluyendo variantes patogénicas detectadas en la mini BD local.
    """
    analysis = (
        db.query(models.Analysis)
        .filter(models.Analysis.id == analysis_id, models.Analysis.patient_id == patient_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado para este paciente.")

    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente no encontrado.")

    details = _safe_load_details(getattr(analysis, "details", None))
    brca1 = details.get("brca1") or {}
    brca2 = details.get("brca2") or {}
    pv_all = (details.get("pathogenic_variants") or {})
    pv_brca1 = pv_all.get("BRCA1") or []
    pv_brca2 = pv_all.get("BRCA2") or []
    pv_list = pv_brca1 + pv_brca2

    snv_count_brca1 = int(brca1.get("snv_count") or 0)
    snv_count_brca2 = int(brca2.get("snv_count") or 0)

    # ----------------------------------------------------------------
    # Construcción del PDF
    # ----------------------------------------------------------------
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Encabezado
    pdf.setTitle("Oncoatlas - Informe germinal BRCA1/BRCA2")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(25 * mm, height - 25 * mm, "Oncoatlas")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(25 * mm, height - 30 * mm, "Informe de análisis germinal BRCA1/BRCA2")

    pdf.line(25 * mm, height - 32 * mm, width - 25 * mm, height - 32 * mm)

    y = height - 40 * mm

    # Datos del paciente
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(25 * mm, y, "Datos del paciente")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    full_name = getattr(patient, "full_name", "N/D")
    document_id = getattr(patient, "document_id", "N/D")
    sex = getattr(patient, "sex", None) or "N/D"
    dob = getattr(patient, "date_of_birth", None)
    if hasattr(dob, "strftime"):
        dob_str = dob.strftime("%d/%m/%Y")
    else:
        dob_str = str(dob) if dob else "N/D"

    pdf.drawString(25 * mm, y, f"Nombre: {full_name}")
    y -= 5 * mm
    pdf.drawString(25 * mm, y, f"Documento: {document_id}")
    y -= 5 * mm
    pdf.drawString(25 * mm, y, f"Sexo biológico: {sex}")
    y -= 5 * mm
    pdf.drawString(25 * mm, y, f"Fecha de nacimiento: {dob_str}")
    y -= 8 * mm

    # Datos del análisis
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(25 * mm, y, "Datos del análisis")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    created_at = getattr(analysis, "created_at", None)
    if hasattr(created_at, "strftime"):
        created_str = created_at.strftime("%d/%m/%Y %H:%M")
    else:
        created_str = str(created_at) if created_at else "N/D"

    status = getattr(analysis, "status", "N/D")
    summary = getattr(analysis, "summary", "Sin resumen disponible.")

    pdf.drawString(25 * mm, y, f"ID de análisis: {analysis.id}")
    y -= 5 * mm
    pdf.drawString(25 * mm, y, f"Fecha del análisis: {created_str}")
    y -= 5 * mm
    pdf.drawString(25 * mm, y, f"Estado: {status}")
    y -= 7 * mm

    # Resumen clínico
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(25 * mm, y, "Resumen clínico")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    text_obj = pdf.beginText()
    text_obj.setTextOrigin(25 * mm, y)
    text_obj.setLeading(12)
    for line in _wrap_text(summary, max_chars=100):
        text_obj.textLine(line)
    pdf.drawText(text_obj)
    y = text_obj.getY() - 8

    if y < 60 * mm:
        pdf.showPage()
        y = height - 30 * mm

    # Conteo global de SNV
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(25 * mm, y, "Conteo global de variantes (SNV)")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(30 * mm, y, f"BRCA1: {snv_count_brca1} SNV")
    y -= 5 * mm
    pdf.drawString(30 * mm, y, f"BRCA2: {snv_count_brca2} SNV")
    y -= 8 * mm

    if y < 60 * mm:
        pdf.showPage()
        y = height - 30 * mm

    # Variantes patogénicas (mini BD local)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(25 * mm, y, "Variantes patogénicas (mini BD local Oncoatlas)")
    y -= 6 * mm

    pdf.setFont("Helvetica", 10)

    if not pv_list:
        pdf.drawString(
            30 * mm,
            y,
            "No se identificaron variantes con anotación clínica en la mini base de datos local "
            "para estas secuencias."
        )
        y -= 10 * mm
    else:
        for hit in pv_list:
            if y < 40 * mm:
                pdf.showPage()
                y = height - 30 * mm
                pdf.setFont("Helvetica", 10)

            gene = hit.get("gene", "")
            short_name = hit.get("short_name", "")
            hgvs_c = hit.get("hgvs_c", "")
            hgvs_p = hit.get("hgvs_p", "")
            variant_type = hit.get("variant_type", "")
            pathogenicity = hit.get("pathogenicity", "")
            cancers = ", ".join(hit.get("main_cancers") or [])
            clinvar_url = hit.get("clinvar_url", "")

            pdf.drawString(
                30 * mm,
                y,
                f"{gene} {short_name} ({hgvs_c}, {hgvs_p})"
            )
            y -= 5 * mm
            pdf.drawString(
                34 * mm,
                y,
                f"Tipo de variante: {variant_type} · Significado clínico: {pathogenicity}"
            )
            y -= 5 * mm
            if cancers:
                pdf.drawString(
                    34 * mm,
                    y,
                    f"Cáncer(es) asociado(s): {cancers}"
                )
                y -= 5 * mm
            if clinvar_url:
                pdf.drawString(
                    34 * mm,
                    y,
                    f"ClinVar: {clinvar_url}"
                )
                y -= 5 * mm

            y -= 4 * mm  # espacio extra entre variantes

    if y < 40 * mm:
        pdf.showPage()
        y = height - 40 * mm
        pdf.setFont("Helvetica", 9)

    # Nota final
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        25 * mm,
        y,
        "Aviso: este informe de Oncoatlas es un prototipo académico. "
    )
    y -= 5 * mm
    pdf.drawString(
        25 * mm,
        y,
        "No debe utilizarse para la toma de decisiones clínicas sin validación "
        "en laboratorio ni revisión por un especialista en genética."
    )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f"oncoatlas_report_patient_{patient_id}_analysis_{analysis_id}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'},
    )
