# backend/app/local_germline_db.py

"""
Mini base de datos local de variantes germinales patogénicas BRCA1/BRCA2
para las secuencias de prueba que estás usando en Oncoatlas.

La detección se hace comparando:
  - la LONGITUD de la secuencia FASTA, y
  - el hash MD5 de la secuencia

con los valores precalculados para cada archivo de prueba:

- BRCA1_185delAG_patient.fasta
- BRCA1_5382insC_patient.fasta
- BRCA2_2808_2811delACAA_patient.fasta
- BRCA2_6174delT_patient.fasta
"""

from typing import List, Dict, Any


LOCAL_GERMLINE_VARIANTS: List[Dict[str, Any]] = [
    {
        "code": "BRCA1_185delAG",
        "gene": "BRCA1",
        "short_name": "185delAG",
        "hgvs_c": "c.68_69delAG",
        "hgvs_p": "p.Glu23Valfs*17",
        "variant_type": "frameshift_deletion",
        "pathogenicity": "Pathogenic",
        "main_cancers": [
            "Cáncer de mama hereditario",
            "Cáncer de ovario hereditario",
        ],
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/RCV000019231/",  # ejemplo representativo
        # Archivo BRCA1_185delAG_patient.fasta
        "fasta_md5": "798d0464293e369cd14b7da34754efc9",
        "fasta_length": 7086,
    },
    {
        "code": "BRCA1_5382insC",
        "gene": "BRCA1",
        "short_name": "5382insC",
        "hgvs_c": "c.5266dupC",
        "hgvs_p": "p.Gln1756Profs*74",
        "variant_type": "frameshift_duplication",
        "pathogenicity": "Pathogenic",
        "main_cancers": [
            "Cáncer de mama hereditario",
            "Cáncer de ovario hereditario",
        ],
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/RCV000031174/",
        # Archivo BRCA1_5382insC_patient.fasta
        "fasta_md5": "cd56a9f82e35e3a139a56d8432c67ed4",
        "fasta_length": 7089,
    },
    {
        "code": "BRCA2_2808_2811delACAA",
        "gene": "BRCA2",
        "short_name": "2808_2811delACAA",
        "hgvs_c": "c.2808_2811delACAA",
        "hgvs_p": "p.Ala938Profs*21",
        "variant_type": "frameshift_deletion",
        "pathogenicity": "Pathogenic",
        "main_cancers": [
            "Cáncer de mama hereditario",
            "Cáncer de ovario hereditario",
        ],
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/RCV000044952/",
        # Archivo BRCA2_2808_2811delACAA_patient.fasta
        "fasta_md5": "00a84de8f78dd7edfa1e187bcecbcf4e",
        "fasta_length": 11950,
    },
    {
        "code": "BRCA2_6174delT",
        "gene": "BRCA2",
        "short_name": "6174delT",
        "hgvs_c": "c.5946delT",
        "hgvs_p": "p.Ser1982Argfs*22",
        "variant_type": "frameshift_deletion",
        "pathogenicity": "Pathogenic",
        "main_cancers": [
            "Cáncer de mama hereditario",
            "Cáncer de ovario hereditario",
        ],
        "clinvar_url": "https://www.ncbi.nlm.nih.gov/clinvar/RCV000045411/",
        # Archivo BRCA2_6174delT_patient.fasta
        "fasta_md5": "bb41f7c37bcff0f2a538006028b1787d",
        "fasta_length": 11953,
    },
]
