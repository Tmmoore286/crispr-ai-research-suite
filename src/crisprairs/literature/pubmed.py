"""PubMed E-utilities client for evidence retrieval."""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any

import requests

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TIMEOUT = 10

_MODALITY_TERMS = {
    "knockout": "gene knockout",
    "base_editing": "base editing",
    "prime_editing": "prime editing",
    "activation": "CRISPR activation",
    "repression": "CRISPR interference",
    "off_target": "off-target",
    "troubleshoot": "optimization troubleshooting",
}


def build_query_from_context(ctx) -> str:
    """Build a focused PubMed query from session context."""
    terms: list[str] = ["CRISPR"]

    target_gene = str(getattr(ctx, "target_gene", "") or "").strip()
    species = str(getattr(ctx, "species", "") or "").strip()
    modality = str(getattr(ctx, "modality", "") or "").strip().lower()
    issue = str(getattr(ctx, "troubleshoot_issue", "") or "").strip().replace("_", " ")

    if target_gene:
        terms.append(target_gene)
    if species:
        terms.append(species)
    if modality in _MODALITY_TERMS:
        terms.append(_MODALITY_TERMS[modality])
    if issue:
        terms.append(issue)

    unique_terms = list(OrderedDict((term, None) for term in terms).keys())
    return " AND ".join(f"({term})" for term in unique_terms if term)


def search_ids(query: str, retmax: int = 12, sort: str = "relevance") -> list[str]:
    """Search PubMed and return PMID list."""
    if not query.strip():
        return []

    try:
        response = requests.get(
            f"{EUTILS_BASE}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": retmax,
                "sort": sort,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.error("PubMed esearch error: %s", exc)
        return []

    return [str(i) for i in payload.get("esearchresult", {}).get("idlist", [])]


def fetch_summaries(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch summary metadata for PMIDs."""
    if not pmids:
        return []

    try:
        response = requests.get(
            f"{EUTILS_BASE}/esummary.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.error("PubMed esummary error: %s", exc)
        return []

    result = payload.get("result", {})
    ids = [str(uid) for uid in result.get("uids", [])]

    hits: list[dict[str, Any]] = []
    for uid in ids:
        row = result.get(uid, {})
        if not row:
            continue
        authors = [a.get("name", "") for a in row.get("authors", []) if a.get("name")]
        hits.append(
            {
                "pmid": uid,
                "title": row.get("title", ""),
                "journal": row.get("fulljournalname") or row.get("source", ""),
                "pubdate": row.get("pubdate", ""),
                "authors": authors[:5],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "source": "pubmed",
            }
        )
    return hits


def fetch_pubmed_hits(query: str, retmax: int = 8) -> list[dict[str, Any]]:
    """Fetch a blend of relevant and recent PubMed papers."""
    relevant = search_ids(query, retmax=retmax, sort="relevance")
    recent = search_ids(query, retmax=retmax, sort="date")

    merged: list[str] = []
    seen: set[str] = set()
    for pmid in relevant + recent:
        if pmid in seen:
            continue
        seen.add(pmid)
        merged.append(pmid)
        if len(merged) >= retmax:
            break

    return fetch_summaries(merged)
