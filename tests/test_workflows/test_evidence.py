"""Tests for evidence workflow step."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.evidence import EvidenceRiskStep, EvidenceScanStep


class TestEvidenceScanStep:
    def test_populates_context_with_hits(self):
        ctx = SessionContext(target_gene="TP53", species="human", modality="knockout")
        step = EvidenceScanStep()
        payload = {
            "query": "(CRISPR) AND (TP53)",
            "source": "pubmed",
            "hits": [
                {
                    "pmid": "123",
                    "title": "CRISPR editing in TP53",
                    "journal": "Nature",
                    "pubdate": "2025",
                }
            ],
            "notes": ["Review newest studies."],
        }

        with patch("crisprairs.workflows.evidence.run_literature_scan", return_value=payload):
            out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert ctx.literature_query == payload["query"]
        assert len(ctx.literature_hits) == 1
        assert ctx.evidence_metrics["papers_found"] == 1
        assert "PMID 123" in out.message

    def test_handles_empty_scan(self):
        ctx = SessionContext(modality="troubleshoot")
        step = EvidenceScanStep()

        with patch(
            "crisprairs.workflows.evidence.run_literature_scan",
            return_value={"query": "", "source": "pubmed", "hits": [], "notes": ["No hits"]},
        ):
            out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert ctx.literature_hits == []
        assert "No papers were returned" in out.message


class TestEvidenceRiskStep:
    def test_populates_risk_metrics(self):
        ctx = SessionContext(target_gene="TP53")
        ctx.literature_hits = [{"pmid": "1", "title": "paper"}]
        step = EvidenceRiskStep()
        review = {
            "papers_reviewed": 1,
            "papers_flagged": 1,
            "risks": ["1 paper(s) include cautionary language (toxicity/off-target/genomic risk)."],
            "hits": [{"pmid": "1", "title": "paper", "risk_terms": ["off-target"]}],
        }

        with patch("crisprairs.workflows.evidence.run_evidence_risk_review", return_value=review):
            out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert ctx.evidence_metrics["papers_reviewed"] == 1
        assert ctx.evidence_metrics["papers_flagged"] == 1
        assert "Evidence Risk Review" in out.message
