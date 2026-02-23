"""Tests for literature/pubmed.py."""

from unittest.mock import MagicMock, patch

from crisprairs.engine.context import SessionContext
from crisprairs.literature.pubmed import (
    build_query_from_context,
    fetch_pubmed_hits,
    fetch_summaries,
    search_ids,
)


class TestBuildQueryFromContext:
    def test_builds_query_with_core_fields(self):
        ctx = SessionContext(
            target_gene="TP53",
            species="human",
            modality="knockout",
        )
        query = build_query_from_context(ctx)
        assert "CRISPR" in query
        assert "TP53" in query
        assert "human" in query
        assert "gene knockout" in query

    def test_includes_troubleshoot_issue(self):
        ctx = SessionContext(modality="troubleshoot", troubleshoot_issue="low_efficiency")
        query = build_query_from_context(ctx)
        assert "low efficiency" in query


class TestSearchIds:
    def test_returns_id_list(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"esearchresult": {"idlist": ["1", "2", "3"]}}

        with patch("crisprairs.literature.pubmed.requests.get", return_value=mock_resp):
            ids = search_ids("CRISPR AND TP53")

        assert ids == ["1", "2", "3"]

    def test_handles_request_error(self):
        import requests

        with patch(
            "crisprairs.literature.pubmed.requests.get",
            side_effect=requests.RequestException("boom"),
        ):
            ids = search_ids("CRISPR")
        assert ids == []


class TestFetchSummaries:
    def test_parses_summary_rows(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "result": {
                "uids": ["123"],
                "123": {
                    "title": "CRISPR editing in human cells",
                    "fulljournalname": "Nature Biotechnology",
                    "pubdate": "2025 Jan",
                    "authors": [{"name": "Smith J"}, {"name": "Lee A"}],
                },
            }
        }

        with patch("crisprairs.literature.pubmed.requests.get", return_value=mock_resp):
            hits = fetch_summaries(["123"])

        assert len(hits) == 1
        assert hits[0]["pmid"] == "123"
        assert "CRISPR editing" in hits[0]["title"]
        assert hits[0]["url"].endswith("/123/")


class TestFetchPubMedHits:
    def test_blends_recent_and_relevant(self):
        with patch(
            "crisprairs.literature.pubmed.search_ids",
            side_effect=[["1", "2", "3"], ["3", "4", "5"]],
        ):
            with patch(
                "crisprairs.literature.pubmed.fetch_summaries",
                return_value=[{"pmid": "1"}, {"pmid": "2"}, {"pmid": "3"}],
            ) as mock_summaries:
                hits = fetch_pubmed_hits("CRISPR", retmax=3)

        assert len(hits) == 3
        called_pmids = mock_summaries.call_args[0][0]
        assert called_pmids == ["1", "2", "3"]
