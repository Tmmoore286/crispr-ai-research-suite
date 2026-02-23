"""Tests for literature/service.py."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.literature.service import build_gap_notes, run_literature_scan


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
