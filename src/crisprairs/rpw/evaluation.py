"""Session-level quality metrics for evidence-assisted workflows."""

from __future__ import annotations

from typing import Any


def compute_session_quality_metrics(ctx) -> dict[str, Any]:
    """Compute evidence/reproducibility metrics for one session context."""
    hits = list(getattr(ctx, "literature_hits", []) or [])
    existing = dict(getattr(ctx, "evidence_metrics", {}) or {})

    priorities = [
        float(h.get("priority_score", 0.0))
        for h in hits
        if h.get("priority_score") is not None
    ]
    unique_pmids = {str(h.get("pmid", "")).strip() for h in hits if h.get("pmid")}
    hits_with_entities = sum(1 for h in hits if h.get("entities"))
    hits_with_icite = sum(1 for h in hits if h.get("icite"))

    result = {
        "papers_found": len(hits),
        "unique_pmids": len(unique_pmids),
        "papers_flagged": int(existing.get("papers_flagged", 0) or 0),
        "papers_reviewed": int(existing.get("papers_reviewed", len(hits)) or 0),
        "hits_with_entities": hits_with_entities,
        "hits_with_icite": hits_with_icite,
        "mean_priority_score": round(sum(priorities) / len(priorities), 3) if priorities else 0.0,
        "reproducibility_core_fields": all(
            bool(str(getattr(ctx, field, "") or "").strip())
            for field in ("target_gene", "species", "modality")
        ),
    }
    result.update(existing)
    return result


def aggregate_quality_metrics(metrics_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate quality metrics across multiple sessions."""
    if not metrics_rows:
        return {
            "sessions": 0,
            "avg_papers_found": 0.0,
            "avg_flagged": 0.0,
            "avg_priority": 0.0,
            "pct_core_fields_complete": 0.0,
        }

    sessions = len(metrics_rows)
    avg_papers_found = sum(float(m.get("papers_found", 0) or 0) for m in metrics_rows) / sessions
    avg_flagged = sum(float(m.get("papers_flagged", 0) or 0) for m in metrics_rows) / sessions
    avg_priority = (
        sum(float(m.get("mean_priority_score", 0.0) or 0.0) for m in metrics_rows) / sessions
    )
    core_ok = sum(1 for m in metrics_rows if bool(m.get("reproducibility_core_fields")))

    return {
        "sessions": sessions,
        "avg_papers_found": round(avg_papers_found, 3),
        "avg_flagged": round(avg_flagged, 3),
        "avg_priority": round(avg_priority, 3),
        "pct_core_fields_complete": round((core_ok / sessions) * 100, 1),
    }
