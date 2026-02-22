"""Tests for apis/ncbi.py — NCBI Entrez gene lookup via Biopython."""

import json
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from crisprairs.apis.ncbi import SPECIES_TAXID, fetch_gene_info, fetch_gene_sequence


class TestFetchGeneInfo:
    def test_returns_gene_info(self):
        mock_search = MagicMock()
        mock_search.__enter__ = MagicMock(return_value=mock_search)
        mock_search.__exit__ = MagicMock(return_value=False)

        mock_summary = MagicMock()
        summary_json = json.dumps({
            "result": {
                "7157": {
                    "name": "TP53",
                    "description": "tumor protein p53",
                    "chromosome": "17",
                    "organism": {"scientificname": "Homo sapiens"},
                    "otheraliases": "p53, LFS1",
                    "summary": "Tumor suppressor gene",
                    "genomicinfo": [],
                }
            }
        })
        mock_summary.__enter__ = MagicMock(return_value=StringIO(summary_json))
        mock_summary.__exit__ = MagicMock(return_value=False)

        with patch("crisprairs.apis.ncbi._configure_entrez") as mock_entrez_fn:
            mock_entrez = MagicMock()
            mock_entrez.esearch.return_value = mock_search
            mock_entrez.read.return_value = {"IdList": ["7157"]}
            mock_entrez.esummary.return_value = mock_summary
            mock_entrez_fn.return_value = mock_entrez

            result = fetch_gene_info("TP53", "human")

        assert result is not None
        assert result["gene_id"] == "7157"
        assert result["symbol"] == "TP53"
        assert result["chromosome"] == "17"

    def test_returns_none_when_not_found(self):
        mock_search = MagicMock()
        mock_search.__enter__ = MagicMock(return_value=mock_search)
        mock_search.__exit__ = MagicMock(return_value=False)

        with patch("crisprairs.apis.ncbi._configure_entrez") as mock_entrez_fn:
            mock_entrez = MagicMock()
            mock_entrez.esearch.return_value = mock_search
            mock_entrez.read.return_value = {"IdList": []}
            mock_entrez_fn.return_value = mock_entrez

            result = fetch_gene_info("FAKEGENE", "human")

        assert result is None

    def test_returns_none_on_error(self):
        with patch("crisprairs.apis.ncbi._configure_entrez") as mock_entrez_fn:
            mock_entrez = MagicMock()
            mock_entrez.esearch.side_effect = Exception("Network error")
            mock_entrez_fn.return_value = mock_entrez

            result = fetch_gene_info("TP53", "human")

        assert result is None


class TestSpeciesTaxid:
    def test_human_taxid(self):
        assert SPECIES_TAXID["human"] == "9606"

    def test_mouse_taxid(self):
        assert SPECIES_TAXID["mouse"] == "10090"


class TestFetchGeneSequence:
    def test_fetch_gene_sequence_resolves_nuccore_from_gene_id(self):
        mock_elink = MagicMock()
        mock_elink.__enter__ = MagicMock(return_value=mock_elink)
        mock_elink.__exit__ = MagicMock(return_value=False)

        mock_efetch = MagicMock()
        mock_efetch.__enter__ = MagicMock(return_value=StringIO(">id\nATCGATCG"))
        mock_efetch.__exit__ = MagicMock(return_value=False)

        with patch("crisprairs.apis.ncbi._configure_entrez") as mock_entrez_fn:
            mock_entrez = MagicMock()
            mock_entrez.elink.return_value = mock_elink
            mock_entrez.efetch.return_value = mock_efetch
            mock_entrez.read.return_value = [
                {
                    "LinkSetDb": [
                        {
                            "LinkName": "gene_nuccore_refseqgenomic",
                            "Link": [{"Id": "NC_000017.11"}],
                        }
                    ]
                }
            ]
            mock_entrez_fn.return_value = mock_entrez

            record = MagicMock()
            record.seq = "ATCGATCG"
            fake_seqio = SimpleNamespace(read=MagicMock(return_value=record))
            fake_bio = SimpleNamespace(SeqIO=fake_seqio)
            with patch.dict(
                "sys.modules",
                {"Bio": fake_bio, "Bio.SeqIO": fake_seqio},
            ):
                sequence = fetch_gene_sequence("7157")

        assert sequence == "ATCGATCG"
        mock_entrez.efetch.assert_called_once_with(
            db="nuccore", id="NC_000017.11", rettype="fasta", retmode="text"
        )

    def test_fetch_gene_sequence_returns_none_when_no_linked_sequence(self):
        mock_elink = MagicMock()
        mock_elink.__enter__ = MagicMock(return_value=mock_elink)
        mock_elink.__exit__ = MagicMock(return_value=False)

        with patch("crisprairs.apis.ncbi._configure_entrez") as mock_entrez_fn:
            mock_entrez = MagicMock()
            mock_entrez.elink.return_value = mock_elink
            mock_entrez.read.return_value = [{"LinkSetDb": []}]
            mock_entrez_fn.return_value = mock_entrez

            sequence = fetch_gene_sequence("7157")

        assert sequence is None
        mock_entrez.efetch.assert_not_called()
