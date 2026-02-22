"""Tests for apis/crispor.py — CRISPOR guide scoring API client."""

from unittest.mock import MagicMock, patch

from crisprairs.apis.crispor import (
    _parse_response,
    design_guides,
    genome_for_species,
    is_available,
    score_existing_guides,
)

MOCK_TSV = (
    "guideSeq\tpam\tposition\tmitSpecScore\tdoench2016Score\t"
    "morenoMateosScore\tofftargetCount\n"
    "ATCGATCGATCGATCGATCG\tNGG\tchr17:100\t85.2\t62.1\t55.0\t3\n"
    "GCTAGCTAGCTAGCTAGCTA\tNGG\tchr17:200\t72.5\t58.3\t48.0\t7\n"
)


class TestGenomeForSpecies:
    def test_human(self):
        assert genome_for_species("human") == "hg38"

    def test_mouse(self):
        assert genome_for_species("mouse") == "mm10"

    def test_unknown_passes_through(self):
        assert genome_for_species("danRer11") == "danRer11"


class TestDesignGuides:
    def test_returns_parsed_guides(self):
        mock_resp = MagicMock()
        mock_resp.text = MOCK_TSV
        mock_resp.raise_for_status = MagicMock()

        with patch("crisprairs.apis.crispor.requests.get", return_value=mock_resp):
            guides = design_guides("ATCG" * 50, species="human")

        assert len(guides) == 2
        assert guides[0]["guide_sequence"] == "ATCGATCGATCGATCGATCG"
        assert guides[0]["mit_specificity_score"] == 85.2
        assert guides[1]["off_target_count"] == 7

    def test_returns_empty_on_timeout(self):
        import requests
        with patch("crisprairs.apis.crispor.requests.get", side_effect=requests.Timeout):
            guides = design_guides("ATCG" * 50)
        assert guides == []

    def test_returns_empty_on_network_error(self):
        import requests
        with patch("crisprairs.apis.crispor.requests.get", side_effect=requests.ConnectionError):
            guides = design_guides("ATCG" * 50)
        assert guides == []


class TestScoreExistingGuides:
    def test_scores_multiple_guides(self):
        mock_resp = MagicMock()
        mock_resp.text = MOCK_TSV
        mock_resp.raise_for_status = MagicMock()

        with patch("crisprairs.apis.crispor.requests.get", return_value=mock_resp):
            results = score_existing_guides(["ATCG" * 5, "GCTA" * 5], species="human")

        assert len(results) == 2
        assert results[0]["query_sequence"] == "ATCG" * 5


class TestIsAvailable:
    def test_available(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("crisprairs.apis.crispor.requests.get", return_value=mock_resp):
            assert is_available() is True

    def test_unavailable(self):
        import requests
        with patch("crisprairs.apis.crispor.requests.get", side_effect=requests.ConnectionError):
            assert is_available() is False


class TestParseResponse:
    def test_parses_tsv(self):
        guides = _parse_response(MOCK_TSV)
        assert len(guides) == 2
        assert guides[0]["pam"] == "NGG"

    def test_empty_response(self):
        assert _parse_response("") == []
