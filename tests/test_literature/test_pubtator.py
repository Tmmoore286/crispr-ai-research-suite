"""Tests for literature/pubtator.py."""

from unittest.mock import MagicMock, patch

from crisprairs.literature.pubtator import fetch_entity_annotations


class TestFetchEntityAnnotations:
    def test_parses_entities_by_type(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {
                "id": "123",
                "passages": [
                    {
                        "annotations": [
                            {"text": "TP53", "infons": {"type": "Gene"}},
                            {"text": "cancer", "infons": {"type": "Disease"}},
                        ]
                    }
                ],
            }
        ]

        with patch("crisprairs.literature.pubtator.requests.get", return_value=mock_resp):
            entities = fetch_entity_annotations(["123"])

        assert entities["123"]["Gene"] == ["TP53"]
        assert entities["123"]["Disease"] == ["cancer"]

    def test_returns_empty_on_request_error(self):
        import requests

        with patch(
            "crisprairs.literature.pubtator.requests.get",
            side_effect=requests.RequestException("boom"),
        ):
            entities = fetch_entity_annotations(["123"])
        assert entities == {}
