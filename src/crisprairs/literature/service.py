"""Evidence scan service built on PubMed retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from crisprairs.literature.pubmed import build_query_from_context, fetch_pubmed_hits


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
