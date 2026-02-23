"""Evidence scan service built on PubMed retrieval."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from math import log1p
from typing import Any

from crisprairs.literature.icite import fetch_icite_metrics
from crisprairs.literature.pubmed import build_query_from_context, fetch_pubmed_hits
from crisprairs.literature.pubtator import fetch_entity_annotations

RISK_TERMS = (
    "off-target",
    "toxicity",
    "genotoxic",
    "chromothripsis",
    "rearrangement",
    "immune",
    "oncogenic",
    "low efficiency",
    "poor efficiency",
)


def run_literature_scan(ctx, max_hits: int = 8) -> dict[str, Any]:
    """Run a PubMed-based evidence scan for the current context."""
    query = build_query_from_context(ctx)
    scan = {
        "query": query,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": "pubmed",
        "hits": [],
        "notes": [],
    }

    if not query:
        scan["notes"] = ["Not enough context to build a literature query."]
        return scan

    hits = fetch_pubmed_hits(query, retmax=max_hits)
    hits = enrich_hits_with_pubtator(hits)
    hits = enrich_hits_with_icite(hits)
    hits = sort_hits_by_priority(hits)
    scan["hits"] = hits
    scan["notes"] = build_gap_notes(ctx, hits)
    return scan


def build_gap_notes(ctx, hits: list[dict[str, Any]]) -> list[str]:
    """Generate concise 'what may be missing' notes."""
    notes: list[str] = []
    modality = str(getattr(ctx, "modality", "") or "")
    species = str(getattr(ctx, "species", "") or "")

    if not hits:
        notes.append("No PubMed hits returned for the current query.")
        return notes

    if len(hits) < 3:
        notes.append("Low hit count; broaden search terms or include synonyms.")

    if not species:
        notes.append("Species not set; evidence may include mixed model systems.")

    if modality in {"off_target", "base_editing", "prime_editing"}:
        notes.append("Review newest papers for modality-specific risk profiles.")

    if not any(hit.get("icite") for hit in hits):
        notes.append("iCite metrics were unavailable; ranking uses limited evidence signals.")

    return notes


def enrich_hits_with_pubtator(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach PubTator entity annotations to each hit."""
    if not hits:
        return []
    pmids = [str(hit.get("pmid", "")).strip() for hit in hits if hit.get("pmid")]
    annotations = fetch_entity_annotations(pmids)

    enriched: list[dict[str, Any]] = []
    for hit in hits:
        row = dict(hit)
        pmid = str(row.get("pmid", "")).strip()
        row["entities"] = annotations.get(pmid, {})
        enriched.append(row)
    return enriched


def enrich_hits_with_icite(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach iCite triage metrics and computed priority score."""
    if not hits:
        return []

    pmids = [str(hit.get("pmid", "")).strip() for hit in hits if hit.get("pmid")]
    metrics = fetch_icite_metrics(pmids)

    enriched: list[dict[str, Any]] = []
    for hit in hits:
        row = dict(hit)
        pmid = str(row.get("pmid", "")).strip()
        i_metrics = metrics.get(pmid, {})
        row["icite"] = i_metrics
        row["priority_score"] = compute_priority_score(row)
        enriched.append(row)
    return enriched


def sort_hits_by_priority(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort hits by descending priority score."""
    return sorted(
        hits,
        key=lambda hit: float(hit.get("priority_score", 0.0)),
        reverse=True,
    )


def compute_priority_score(hit: dict[str, Any]) -> float:
    """Compute triage score from iCite metrics and recency."""
    icite = hit.get("icite", {}) or {}
    rcr = float(icite.get("rcr") or 0.0)
    apt = float(icite.get("apt") or 0.0)
    citations = int(icite.get("citations") or 0)

    pub_year = _extract_year(str(hit.get("pubdate", "") or ""))
    now_year = datetime.now(timezone.utc).year
    age = max(now_year - pub_year, 0) if pub_year else 10
    recency_bonus = max(0.0, (8 - age) * 0.25)

    return round((rcr * 1.4) + (apt * 0.9) + log1p(citations) + recency_bonus, 3)


def _extract_year(pubdate: str) -> int | None:
    match = re.search(r"\b(19|20)\d{2}\b", pubdate)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def run_evidence_risk_review(ctx) -> dict[str, Any]:
    """Run a final risk-oriented evidence pass before workflow completion."""
    hits = [dict(h) for h in (ctx.literature_hits or [])]
    risks: list[str] = []
    flagged = 0

    target_gene = str(getattr(ctx, "target_gene", "") or "").lower().strip()

    for hit in hits:
        title = str(hit.get("title", ""))
        lowered = title.lower()
        risk_terms = sorted(term for term in RISK_TERMS if term in lowered)
        if risk_terms:
            flagged += 1
            hit["risk_terms"] = risk_terms
        else:
            hit["risk_terms"] = []

    if not hits:
        risks.append("No literature evidence available; manual review recommended.")
    else:
        if flagged:
            risks.append(
                f"{flagged} paper(s) include cautionary language "
                "(toxicity/off-target/genomic risk)."
            )
        if target_gene and not any(target_gene in str(h.get("title", "")).lower() for h in hits):
            risks.append(
                "No top hits explicitly mention the target gene; "
                "expand synonyms and related pathway terms."
            )
        if not any(h.get("entities", {}).get("Gene") for h in hits):
            risks.append(
                "PubTator did not return gene entities in top hits; "
                "review search specificity."
            )

    review = {
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "papers_reviewed": len(hits),
        "papers_flagged": flagged,
        "risks": risks,
        "hits": hits,
    }
    return review
