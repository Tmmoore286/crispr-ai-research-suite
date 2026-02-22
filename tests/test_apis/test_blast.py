"""Tests for apis/blast.py — NCBI BLAST API client."""

from unittest.mock import patch, MagicMock

from crisprairs.apis.blast import (
    submit_blast,
    poll_results,
    check_primer_specificity,
    _parse_blast_xml,
    ORGANISM_MAP,
)


MOCK_BLAST_XML = """<?xml version="1.0"?>
<BlastOutput>
  <BlastOutput_iterations>
    <Iteration>
      <Iteration_hits>
        <Hit>
          <Hit_accession>NM_000546</Hit_accession>
          <Hit_def>Homo sapiens tumor protein p53 (TP53)</Hit_def>
          <Hit_len>2629</Hit_len>
          <Hit_hsps>
            <Hsp>
              <Hsp_identity>20</Hsp_identity>
              <Hsp_align-len>20</Hsp_align-len>
              <Hsp_evalue>0.001</Hsp_evalue>
              <Hsp_bit-score>40.1</Hsp_bit-score>
            </Hsp>
          </Hit_hsps>
        </Hit>
      </Iteration_hits>
    </Iteration>
  </BlastOutput_iterations>
</BlastOutput>"""


class TestSubmitBlast:
    def test_returns_rid(self):
        mock_resp = MagicMock()
        mock_resp.text = "RID = ABC12345\nRTOE = 30"
        mock_resp.raise_for_status = MagicMock()

        with patch("crisprairs.apis.blast.requests.post", return_value=mock_resp):
            rid = submit_blast("ATCGATCGATCGATCGATCG")

        assert rid == "ABC12345"

    def test_returns_none_on_failure(self):
        import requests
        with patch("crisprairs.apis.blast.requests.post", side_effect=requests.ConnectionError):
            rid = submit_blast("ATCG")
        assert rid is None

    def test_organism_filter(self):
        mock_resp = MagicMock()
        mock_resp.text = "RID = XYZ789\nRTOE = 30"
        mock_resp.raise_for_status = MagicMock()

        with patch("crisprairs.apis.blast.requests.post", return_value=mock_resp) as mock_post:
            submit_blast("ATCG", organism="human")
            call_data = mock_post.call_args[1]["data"]
            assert "Homo sapiens" in call_data.get("ENTREZ_QUERY", "")


class TestPollResults:
    def test_returns_hits_when_ready(self):
        mock_resp = MagicMock()
        mock_resp.text = MOCK_BLAST_XML
        mock_resp.raise_for_status = MagicMock()

        with patch("crisprairs.apis.blast.requests.get", return_value=mock_resp):
            hits = poll_results("ABC12345", max_wait=5)

        assert len(hits) == 1
        assert hits[0]["accession"] == "NM_000546"

    def test_returns_empty_on_failure(self):
        mock_resp = MagicMock()
        mock_resp.text = "Status=FAILED"
        mock_resp.raise_for_status = MagicMock()

        with patch("crisprairs.apis.blast.requests.get", return_value=mock_resp):
            hits = poll_results("FAIL_RID", max_wait=5)

        assert hits == []


class TestCheckPrimerSpecificity:
    def test_specific_primers(self):
        with patch("crisprairs.apis.blast.submit_blast", return_value="RID1"):
            with patch("crisprairs.apis.blast.poll_results", return_value=[{"accession": "NM_000546"}]):
                result = check_primer_specificity("ATCG", "GCTA")

        assert result["specific"] is True
        assert result["forward_hits"] == 1
        assert result["reverse_hits"] == 1

    def test_non_specific_primers(self):
        multi_hits = [{"accession": "NM_001"}, {"accession": "NM_002"}]
        with patch("crisprairs.apis.blast.submit_blast", return_value="RID1"):
            with patch("crisprairs.apis.blast.poll_results", return_value=multi_hits):
                result = check_primer_specificity("ATCG", "GCTA")

        assert result["specific"] is False

    def test_submission_failure(self):
        with patch("crisprairs.apis.blast.submit_blast", return_value=None):
            result = check_primer_specificity("ATCG", "GCTA")
        assert result["specific"] is False


class TestParseBlastXml:
    def test_parses_hits(self):
        hits = _parse_blast_xml(MOCK_BLAST_XML)
        assert len(hits) == 1
        assert hits[0]["accession"] == "NM_000546"
        assert hits[0]["e_value"] == "0.001"

    def test_invalid_xml(self):
        assert _parse_blast_xml("not xml") == []


class TestOrganismMap:
    def test_has_common_species(self):
        assert "human" in ORGANISM_MAP
        assert "mouse" in ORGANISM_MAP
        assert ORGANISM_MAP["human"] == "Homo sapiens"
