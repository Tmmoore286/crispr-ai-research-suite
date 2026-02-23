"""iCite client for literature triage metrics."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

ICITE_API_URL = "https://icite.od.nih.gov/api/pubs"
TIMEOUT = 10


def fetch_icite_metrics(pmids: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch iCite metrics keyed by PMID."""
    clean_pmids = [str(p) for p in pmids if str(p).strip()]
    if not clean_pmids:
        return {}

    try:
        response = requests.get(
            ICITE_API_URL,
            params={"pmids": ",".join(clean_pmids)},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.error("iCite request error: %s", exc)
        return {}
    except ValueError as exc:
        logger.error("iCite JSON parse error: %s", exc)
        return {}

    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {}

    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        pmid = str(row.get("pmid", "")).strip()
        if not pmid:
            continue
        out[pmid] = {
            "rcr": _to_float(row.get("relative_citation_ratio") or row.get("rcr")),
            "apt": _to_float(row.get("apt")),
            "citations": _to_int(row.get("citation_count")),
            "year": _to_int(row.get("year")),
        }
    return out


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
