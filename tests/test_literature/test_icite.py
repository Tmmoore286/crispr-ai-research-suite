"""Tests for literature/icite.py."""

from unittest.mock import MagicMock, patch

from crisprairs.literature.icite import fetch_icite_metrics


class TestFetchICiteMetrics:
    def test_parses_metrics(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "pmid": "123",
                    "rcr": 2.1,
                    "apt": 0.45,
                    "citation_count": 23,
                    "year": 2024,
                }
            ]
        }

        with patch("crisprairs.literature.icite.requests.get", return_value=mock_resp):
            metrics = fetch_icite_metrics(["123"])

        assert metrics["123"]["rcr"] == 2.1
        assert metrics["123"]["apt"] == 0.45
        assert metrics["123"]["citations"] == 23

    def test_handles_request_error(self):
        import requests

        with patch(
            "crisprairs.literature.icite.requests.get",
            side_effect=requests.RequestException("boom"),
        ):
            metrics = fetch_icite_metrics(["123"])
        assert metrics == {}
