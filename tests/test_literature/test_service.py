"""Tests for literature/service.py."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.literature.service import (
    build_gap_notes,
    compute_priority_score,
    enrich_hits_with_icite,
    enrich_hits_with_pubtator,
    run_evidence_risk_review,
    run_literature_scan,
    sort_hits_by_priority,
)


class TestBuildGapNotes:
    def test_notes_for_no_hits(self):
        ctx = SessionContext(modality="knockout")
        notes = build_gap_notes(ctx, [])
        assert any("No PubMed hits" in n for n in notes)

    def test_notes_for_sparse_hits_without_species(self):
        ctx = SessionContext(modality="base_editing")
        notes = build_gap_notes(ctx, [{"pmid": "1"}])
        assert any("Low hit count" in n for n in notes)
        assert any("Species not set" in n for n in notes)


class TestRunLiteratureScan:
    def test_returns_scan_payload(self):
        ctx = SessionContext(target_gene="TP53", species="human", modality="knockout")
        with patch(
            "crisprairs.literature.service.build_query_from_context",
            return_value="(CRISPR) AND (TP53)",
        ):
            with patch(
                "crisprairs.literature.service.fetch_pubmed_hits",
                return_value=[{"pmid": "123", "title": "Paper A"}],
            ):
                with patch(
                    "crisprairs.literature.service.fetch_entity_annotations",
                    return_value={"123": {"Gene": ["TP53"]}},
                ):
                    with patch(
                        "crisprairs.literature.service.fetch_icite_metrics",
                        return_value={"123": {"rcr": 1.2, "apt": 0.4, "citations": 3}},
                    ):
                        scan = run_literature_scan(ctx, max_hits=5)

        assert scan["query"] == "(CRISPR) AND (TP53)"
        assert len(scan["hits"]) == 1
        assert "retrieved_at" in scan

    def test_handles_empty_query(self):
        ctx = SessionContext()
        with patch(
            "crisprairs.literature.service.build_query_from_context",
            return_value="",
        ):
            scan = run_literature_scan(ctx)

        assert scan["hits"] == []
        assert any("Not enough context" in n for n in scan["notes"])


class TestPubTatorEnrichment:
    def test_attaches_entities(self):
        hits = [{"pmid": "123", "title": "A paper"}]
        with patch(
            "crisprairs.literature.service.fetch_entity_annotations",
            return_value={"123": {"Gene": ["TP53"]}},
        ):
            enriched = enrich_hits_with_pubtator(hits)
        assert enriched[0]["entities"]["Gene"] == ["TP53"]


class TestICiteEnrichment:
    def test_adds_priority_scores(self):
        hits = [{"pmid": "123", "title": "A paper", "pubdate": "2025"}]
        with patch(
            "crisprairs.literature.service.fetch_icite_metrics",
            return_value={"123": {"rcr": 2.0, "apt": 0.5, "citations": 20}},
        ):
            enriched = enrich_hits_with_icite(hits)

        assert "priority_score" in enriched[0]
        assert enriched[0]["priority_score"] > 0

    def test_sort_hits_by_priority(self):
        hits = [
            {"pmid": "1", "priority_score": 1.0},
            {"pmid": "2", "priority_score": 5.0},
        ]
        sorted_hits = sort_hits_by_priority(hits)
        assert sorted_hits[0]["pmid"] == "2"

    def test_compute_priority_score_recency_weight(self):
        old = compute_priority_score({"pubdate": "2014", "icite": {"rcr": 1.0, "apt": 0.1}})
        new = compute_priority_score({"pubdate": "2025", "icite": {"rcr": 1.0, "apt": 0.1}})
        assert new > old


class TestEvidenceRiskReview:
    def test_flags_risk_terms_in_titles(self):
        ctx = SessionContext(target_gene="TP53")
        ctx.literature_hits = [
            {"pmid": "1", "title": "CRISPR off-target toxicity in edited cells", "entities": {}}
        ]
        review = run_evidence_risk_review(ctx)
        assert review["papers_flagged"] == 1
        assert any("cautionary language" in risk for risk in review["risks"])
