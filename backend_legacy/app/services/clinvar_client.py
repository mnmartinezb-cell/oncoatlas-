"""
Cliente simplificado de ClinVar para Oncoatlas.

- Busca por HGVS c. usando ESearch + ESummary.
- Devuelve siempre un dict estable con las mismas claves.
- Si ClinVar no trae 'clinical_significance' para variantes BRCA clásicas,
  usamos un OVERRIDE LOCAL para dejarlas como 'Pathogenic' (demo académica).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


# ─────────────────────────────────────────────────────────────
#  Variantes BRCA "clásicas" con override local
#  (para que siempre salgan como Patogénicas en la demo)
# ─────────────────────────────────────────────────────────────

LOCAL_KNOWN_VARIANTS: Dict[str, Dict[str, Any]] = {
    # BRCA1
    "NM_007294.4:c.68_69delAG": {
        "clinical_significance": "Pathogenic",
        "conditions": ["Hereditary breast-ovarian cancer syndrome (BRCA1)"],
    },
    "NM_007294.4:c.5266dupC": {
        "clinical_significance": "Pathogenic",
        "conditions": ["Hereditary breast-ovarian cancer syndrome (BRCA1)"],
    },
    # BRCA2
    "NM_000059.4:c.5946delT": {
        "clinical_significance": "Pathogenic",
        "conditions": ["Hereditary breast-ovarian cancer syndrome (BRCA2)"],
    },
    "NM_000059.3:c.2808_2811delACAA": {
        "clinical_significance": "Pathogenic",
        "conditions": ["Hereditary breast-ovarian cancer syndrome (BRCA2)"],
    },
}


# ─────────────────────────────────────────────────────────────
#  Funciones internas para llamar a la API de NCBI
# ─────────────────────────────────────────────────────────────


def _esearch_hgvs(hgvs: str) -> Optional[str]:
    """
    Busca en ClinVar un ID (UID) usando el HGVS c.
    Devuelve el primer ID o None.
    """
    params = {
        "db": "clinvar",
        "term": hgvs,
        "retmode": "json",
    }
    resp = requests.get(NCBI_ESEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    idlist = data.get("esearchresult", {}).get("idlist") or []
    return idlist[0] if idlist else None


def _esummary_uid(uid: str) -> Dict[str, Any]:
    """
    Obtiene el resumen ClinVar para un UID.
    Devuelve el doc crudo de ClinVar (dict).
    """
    params = {
        "db": "clinvar",
        "id": uid,
        "retmode": "json",
    }
    resp = requests.get(NCBI_ESUMMARY_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("result", {})
    doc = result.get(uid, {})
    return doc


def _parse_summary(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae campos importantes de la respuesta de ESummary.
    La estructura de ClinVar cambia mucho, así que todo es defensivo.
    """
    title = doc.get("title")

    # clinical_significance suele ser un dict con 'description' y 'review_status'
    clin = doc.get("clinical_significance") or {}
    if isinstance(clin, dict):
        significance = clin.get("description")
        review_status = clin.get("review_status")
    else:
        significance = None
        review_status = None

    # condiciones / enfermedades: trait_set es muy variable
    conditions: List[str] = []
    trait_set = doc.get("trait_set") or []
    if isinstance(trait_set, list):
        for t in trait_set:
            # Varias estructuras posibles
            name = None
            if isinstance(t, dict):
                name = t.get("trait_name") or t.get("name")
            if isinstance(name, list) and name:
                conditions.append(str(name[0]))
            elif isinstance(name, str):
                conditions.append(name)

    return {
        "title": title,
        "clinical_significance": significance,
        "review_status": review_status,
        "conditions": conditions,
    }


# ─────────────────────────────────────────────────────────────
#  API principal que usa el resto de Oncoatlas
# ─────────────────────────────────────────────────────────────


def query_clinvar_hgvs(hgvs: str) -> Dict[str, Any]:
    """
    Consulta ClinVar por un HGVS c. (ej: 'NM_007294.4:c.68_69delAG').

    Devuelve SIEMPRE un dict con estas claves:
      - clinvar_id: str | None
      - title: str | None
      - clinical_significance: str | None
      - review_status: str | None
      - conditions: list[str]
      - hgvs_c_primary: str
      - hgvs_c_all: list[str]
      - override_local: bool (True si usamos tabla LOCAL_KNOWN_VARIANTS)
      - error: str | None
    """
    result: Dict[str, Any] = {
        "clinvar_id": None,
        "title": None,
        "clinical_significance": None,
        "review_status": None,
        "conditions": [],
        "hgvs_c_primary": hgvs,
        "hgvs_c_all": [hgvs],
        "override_local": False,
        "error": None,
    }

    try:
        uid = _esearch_hgvs(hgvs)
        if not uid:
            result["error"] = "No ClinVar record found for this HGVS."
            # Aun así intentaremos override local abajo
        else:
            doc = _esummary_uid(uid)
            parsed = _parse_summary(doc)
            result["clinvar_id"] = uid
            result["title"] = parsed["title"]
            result["clinical_significance"] = parsed["clinical_significance"]
            result["review_status"] = parsed["review_status"]
            result["conditions"] = parsed["conditions"]
    except Exception as exc:
        # No queremos que un fallo de red tumbe Oncoatlas
        result["error"] = f"{type(exc).__name__}: {exc}"

    # ── OVERRIDE LOCAL para variantes BRCA clásicas ─────────────────────
    override = LOCAL_KNOWN_VARIANTS.get(hgvs)
    if override:
        # Solo pisamos si ClinVar no da nada útil
        if not result["clinical_significance"]:
            result["clinical_significance"] = override.get("clinical_significance")
        if not result["conditions"]:
            result["conditions"] = list(override.get("conditions", []))
        if not result["review_status"]:
            result["review_status"] = "local_override"
        result["override_local"] = True

    return result

