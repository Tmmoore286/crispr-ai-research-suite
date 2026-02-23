"""Evidence scan service built on PubMed retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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

    hits = enrich_hits_with_pubtator(fetch_pubmed_hits(query, retmax=max_hits))
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
