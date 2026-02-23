"""Tests for rpw/evaluation.py."""

from crisprairs.engine.context import SessionContext
from crisprairs.rpw.evaluation import aggregate_quality_metrics, compute_session_quality_metrics


class TestComputeSessionQualityMetrics:
    def test_computes_core_metrics(self):
        ctx = SessionContext(target_gene="TP53", species="human", modality="knockout")
        ctx.literature_hits = [
            {
                "pmid": "1",
                "priority_score": 3.0,
                "entities": {"Gene": ["TP53"]},
                "icite": {"rcr": 2.0},
            },
            {"pmid": "2", "priority_score": 1.0, "entities": {}, "icite": {}},
        ]
        ctx.evidence_metrics = {"papers_flagged": 1}

        metrics = compute_session_quality_metrics(ctx)
        assert metrics["papers_found"] == 2
        assert metrics["unique_pmids"] == 2
        assert metrics["papers_flagged"] == 1
        assert metrics["hits_with_entities"] == 1
        assert metrics["mean_priority_score"] == 2.0
        assert metrics["reproducibility_core_fields"] is True


class TestAggregateQualityMetrics:
    def test_aggregates_rows(self):
        rows = [
            {
                "papers_found": 2,
                "papers_flagged": 1,
                "mean_priority_score": 2.0,
                "reproducibility_core_fields": True,
            },
            {
                "papers_found": 4,
                "papers_flagged": 0,
                "mean_priority_score": 4.0,
                "reproducibility_core_fields": False,
            },
        ]
        agg = aggregate_quality_metrics(rows)
        assert agg["sessions"] == 2
        assert agg["avg_papers_found"] == 3.0
        assert agg["avg_flagged"] == 0.5
        assert agg["avg_priority"] == 3.0
        assert agg["pct_core_fields_complete"] == 50.0
