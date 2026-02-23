"""Evidence scanning workflow steps."""

from __future__ import annotations

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.literature.service import run_literature_scan


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
        }
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
                lines.append(f"- PMID {pmid}: {title} ({journal}, {pubdate})")
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
