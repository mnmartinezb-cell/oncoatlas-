from fastapi import APIRouter, File, UploadFile

from ..services.analysis_service import analyse_brca1_brca2

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
)


@router.post("/run")
async def run_simple_analysis(
    brca1_file: UploadFile = File(
        ...,
        description="Archivo FASTA del paciente para BRCA1",
    ),
    brca2_file: UploadFile = File(
        ...,
        description="Archivo FASTA del paciente para BRCA2",
    ),
):
    """
    Endpoint sencillo de análisis genético para Oncoatlas.

    - Lee sólo el encabezado de cada archivo FASTA.
    - Extrae el gen (BRCA1 / BRCA2) y el nombre de la mutación.
    - Consulta la mini base de datos local de variantes germinales patogénicas.
    - Devuelve, para cada archivo, si la variante está o no en esa mini BD,
      junto con la clasificación clínica, el riesgo asociado y el enlace a ClinVar.
    """
    result = await analyse_brca1_brca2(brca1_file, brca2_file)
    return result
