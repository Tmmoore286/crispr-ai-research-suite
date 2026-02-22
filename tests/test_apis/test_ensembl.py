"""Tests for apis/ensembl.py — Ensembl REST API client."""

from unittest.mock import patch

from crisprairs.apis.ensembl import (
    find_orthologs,
    get_gene_info,
    get_sequence,
    list_transcripts,
    lookup_gene_id,
    resolve_species,
)


class TestResolveSpecies:
    def test_human(self):
        assert resolve_species("human") == "homo_sapiens"

    def test_mouse(self):
        assert resolve_species("mouse") == "mus_musculus"

    def test_unknown_passes_through(self):
        assert resolve_species("custom_species") == "custom_species"


class TestLookupGeneId:
    def test_returns_gene_id(self):
        mock_data = [
            {"id": "ENSG00000141510", "type": "gene"},
            {"id": "ENST00000269305", "type": "transcript"},
        ]
        with patch("crisprairs.apis.ensembl._get", return_value=mock_data):
            result = lookup_gene_id("TP53", "human")
        assert result == "ENSG00000141510"

    def test_returns_first_if_no_gene_type(self):
        mock_data = [{"id": "ENST00000269305", "type": "transcript"}]
        with patch("crisprairs.apis.ensembl._get", return_value=mock_data):
            result = lookup_gene_id("TP53", "human")
        assert result == "ENST00000269305"

    def test_returns_none_on_failure(self):
        with patch("crisprairs.apis.ensembl._get", return_value=None):
            result = lookup_gene_id("FAKEGENE", "human")
        assert result is None


class TestGetGeneInfo:
    def test_returns_metadata(self):
        mock_data = {
            "id": "ENSG00000141510",
            "display_name": "TP53",
            "biotype": "protein_coding",
            "description": "tumor protein p53",
            "start": 7661779,
            "end": 7687550,
            "strand": -1,
            "seq_region_name": "17",
            "species": "homo_sapiens",
        }
        with patch("crisprairs.apis.ensembl._get", return_value=mock_data):
            result = get_gene_info("ENSG00000141510")
        assert result["display_name"] == "TP53"
        assert result["seq_region"] == "17"

    def test_returns_none_on_failure(self):
        with patch("crisprairs.apis.ensembl._get", return_value=None):
            assert get_gene_info("ENSG000FAKE") is None


class TestGetSequence:
    def test_returns_sequence_info(self):
        mock_data = {
            "id": "ENSG00000141510",
            "desc": "chromosome:17",
            "seq": "ATCG" * 200,
        }
        with patch("crisprairs.apis.ensembl._get", return_value=mock_data):
            result = get_sequence("ENSG00000141510")
        assert result["seq_length"] == 800
        assert len(result["sequence_preview"]) <= 503  # 500 + "..."

    def test_returns_none_on_failure(self):
        with patch("crisprairs.apis.ensembl._get", return_value=None):
            assert get_sequence("FAKE") is None


class TestListTranscripts:
    def test_returns_transcripts(self):
        mock_data = {
            "Transcript": [
                {
                    "id": "ENST00000269305",
                    "biotype": "protein_coding",
                    "is_canonical": 1,
                    "length": 2629,
                },
                {
                    "id": "ENST00000610292",
                    "biotype": "protein_coding",
                    "is_canonical": 0,
                    "length": 1500,
                },
            ]
        }
        with patch("crisprairs.apis.ensembl._get", return_value=mock_data):
            result = list_transcripts("ENSG00000141510")
        assert len(result) == 2
        assert result[0]["is_canonical"] is True

    def test_returns_empty_on_failure(self):
        with patch("crisprairs.apis.ensembl._get", return_value=None):
            assert list_transcripts("FAKE") == []


class TestFindOrthologs:
    def test_returns_orthologs(self):
        mock_data = {
            "data": [{
                "homologies": [
                    {
                        "type": "ortholog_one2one",
                        "target": {
                            "species": "mus_musculus",
                            "id": "ENSMUSG00000059552",
                            "perc_id": 76.5,
                        },
                    }
                ]
            }]
        }
        with patch("crisprairs.apis.ensembl._get", return_value=mock_data):
            result = find_orthologs("ENSG00000141510")
        assert len(result) == 1
        assert result[0]["species"] == "mus_musculus"

    def test_returns_empty_on_failure(self):
        with patch("crisprairs.apis.ensembl._get", return_value=None):
            assert find_orthologs("FAKE") == []
