from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from reportlab.pdfgen import canvas
from io import BytesIO

from app.database import get_db

router = APIRouter(tags=["reports"])


def _choose_id_column(conn) -> str | None:
    """
    Devuelve el nombre de la columna que actúa como ID en germline_analyses.

    - Si existe una columna 'id' o 'analysis_id', la usamos.
    - Si no existe ninguna, devolvemos None y más adelante usamos ROWID.
    """
    result = conn.execute(text("PRAGMA table_info(germline_analyses);")).mappings().all()
    col_names = {row["name"] for row in result}
    if "id" in col_names:
        return "id"
    if "analysis_id" in col_names:
        return "analysis_id"
    # No hay columna de ID explícita: usaremos rowid
    return None


@router.get(
    "/patients/{patient_id}/analyses/{analysis_id}/report-pdf",
    summary="Generate Analysis Report Pdf",
)
def generate_analysis_report_pdf(patient_id: str, analysis_id: int):
    """
    Genera un PDF BRCA1/BRCA2 usando la información guardada en germline_analyses.

    Soporta dos esquemas posibles de la tabla:
    - Con columna id o analysis_id.
    - Sin columna de id (se usa ROWID de SQLite).
    """
    # 1) Leer el registro de la base de datos
    with engine.connect() as conn:
        id_column = _choose_id_column(conn)

        if id_column is None:
            where_clause = "rowid = :analysis_id"
        else:
            where_clause = f"{id_column} = :analysis_id"

        sql = text(
            f"""
            SELECT
                patient_identifier,
                summary,
                brca1_result,
                brca2_result
            FROM germline_analyses
            WHERE patient_identifier = :patient_id
              AND {where_clause}
            """
        )

        row = (
            conn.execute(
                sql, {"patient_id": patient_id, "analysis_id": analysis_id}
            )
            .mappings()
            .first()
        )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un análisis con ese patient_id y analysis_id.",
        )

    # 2) Construir un PDF muy sencillo en memoria
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setTitle("Oncoatlas – Informe de análisis germinal")

    # Cabecera
    y = 800
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Oncoatlas – Informe de análisis germinal BRCA1/BRCA2")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Paciente: {patient_id}")
    y -= 20
    c.drawString(50, y, f"ID de análisis: {analysis_id}")
    y -= 40

    # Resumen
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resumen:")
    y -= 20

    c.setFont("Helvetica", 10)
    text_obj = c.beginText(50, y)
    summary = row.get("summary") or ""
    for line in summary.splitlines():
        text_obj.textLine(line)
    c.drawText(text_obj)

    # Resultados BRCA1 / BRCA2 (texto plano, ya que en BD tenemos JSON o cadenas)
    y -= 120
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resultado BRCA1:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, (row.get("brca1_result") or "")[:120])

    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resultado BRCA2:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, (row.get("brca2_result") or "")[:120])

    c.showPage()
    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="oncoatlas_report_{patient_id}_{analysis_id}.pdf"'
        },
    )
