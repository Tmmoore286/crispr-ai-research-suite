"""Evidence scanning workflow steps."""

from __future__ import annotations

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.literature.service import run_evidence_risk_review, run_literature_scan
from crisprairs.rpw.evaluation import compute_session_quality_metrics


class EvidenceScanStep(WorkflowStep):
    """Run a fast literature scan and attach evidence context to the session."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        scan = run_literature_scan(ctx)
        hits = scan.get("hits", [])

        ctx.literature_query = scan.get("query", "")
        ctx.literature_hits = hits
        ctx.evidence_gaps = scan.get("notes", [])
        ctx.evidence_metrics = {
            "scan_source": scan.get("source", "pubmed"),
            "papers_found": len(hits),
            "papers_ranked": len([h for h in hits if h.get("priority_score") is not None]),
        }
        ctx.evidence_metrics = compute_session_quality_metrics(ctx)
        ctx.extra["evidence_scan"] = scan

        lines = ["## Literature Gap Check", ""]
        if ctx.literature_query:
            lines.append(f"**Query:** `{ctx.literature_query}`")
            lines.append("")

        if hits:
            lines.append("### Top papers to review")
            for hit in hits[:5]:
                title = hit.get("title", "Untitled")
                pmid = hit.get("pmid", "N/A")
                journal = hit.get("journal", "")
                pubdate = hit.get("pubdate", "")
                score = hit.get("priority_score", 0.0)
                rcr = (hit.get("icite", {}) or {}).get("rcr")
                rcr_label = f", RCR={rcr}" if rcr is not None else ""
                lines.append(
                    f"- PMID {pmid}: {title} ({journal}, {pubdate}; priority={score}{rcr_label})"
                )
        else:
            lines.append("*No papers were returned for this query.*")

        if ctx.evidence_gaps:
            lines.extend(["", "### Potential gaps"])
            for note in ctx.evidence_gaps:
                lines.append(f"- {note}")

        return StepOutput(
            result=StepResult.CONTINUE,
            message="\n".join(lines),
            data=scan,
        )


class EvidenceRiskStep(WorkflowStep):
    """Run a risk-focused review of the collected literature evidence."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        review = run_evidence_risk_review(ctx)

        existing_gaps = list(ctx.evidence_gaps or [])
        merged_gaps = existing_gaps + [
            risk for risk in review.get("risks", []) if risk not in existing_gaps
        ]
        ctx.evidence_gaps = merged_gaps
        ctx.literature_hits = review.get("hits", ctx.literature_hits)
        ctx.evidence_metrics.update(
            {
                "papers_reviewed": review.get("papers_reviewed", 0),
                "papers_flagged": review.get("papers_flagged", 0),
            }
        )
        ctx.evidence_metrics = compute_session_quality_metrics(ctx)
        ctx.extra["evidence_risk_review"] = review

        lines = ["## Evidence Risk Review", ""]
        lines.append(f"- Papers reviewed: {review.get('papers_reviewed', 0)}")
        lines.append(f"- Papers flagged: {review.get('papers_flagged', 0)}")

        risks = review.get("risks", [])
        if risks:
            lines.extend(["", "### Flags to address"])
            for risk in risks:
                lines.append(f"- {risk}")
        else:
            lines.append("")
            lines.append("- No major evidence flags detected in current top papers.")

        return StepOutput(
            result=StepResult.CONTINUE,
            message="\n".join(lines),
            data=review,
        )
