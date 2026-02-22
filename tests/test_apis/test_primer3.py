"""Tests for apis/primer3_api.py — Primer3 wrapper."""

import sys
from unittest.mock import MagicMock, patch

from crisprairs.apis.primer3_api import DEFAULT_PARAMS, check_available, design_primers


class TestCheckAvailable:
    def test_returns_bool(self):
        result = check_available()
        assert isinstance(result, bool)


class TestDesignPrimers:
    def test_returns_primers_when_available(self):
        mock_results = {
            "PRIMER_PAIR_NUM_RETURNED": 2,
            "PRIMER_LEFT_0_SEQUENCE": "ATCGATCGATCGATCGATCG",
            "PRIMER_RIGHT_0_SEQUENCE": "GCTAGCTAGCTAGCTAGCTA",
            "PRIMER_LEFT_0_TM": 60.5,
            "PRIMER_RIGHT_0_TM": 59.8,
            "PRIMER_LEFT_0_GC_PERCENT": 50.0,
            "PRIMER_RIGHT_0_GC_PERCENT": 50.0,
            "PRIMER_PAIR_0_PRODUCT_SIZE": 350,
            "PRIMER_LEFT_1_SEQUENCE": "AAACCCGGGTTTT",
            "PRIMER_RIGHT_1_SEQUENCE": "TTTGGGCCCAAAA",
            "PRIMER_LEFT_1_TM": 61.2,
            "PRIMER_RIGHT_1_TM": 60.1,
            "PRIMER_LEFT_1_GC_PERCENT": 46.0,
            "PRIMER_RIGHT_1_GC_PERCENT": 46.0,
            "PRIMER_PAIR_1_PRODUCT_SIZE": 400,
        }

        # Create a mock primer3 module and inject it into sys.modules
        mock_primer3 = MagicMock()
        mock_primer3.design_primers = MagicMock(return_value=mock_results)

        with patch("crisprairs.apis.primer3_api.check_available", return_value=True):
            with patch.dict(sys.modules, {"primer3": mock_primer3}):
                pairs = design_primers("ATCG" * 100, 150, 23, num_return=2)

        assert len(pairs) == 2
        assert pairs[0]["forward_seq"] == "ATCGATCGATCGATCGATCG"
        assert pairs[0]["product_size"] == 350
        assert pairs[1]["forward_tm"] == 61.2

    def test_returns_empty_when_not_installed(self):
        with patch("crisprairs.apis.primer3_api.check_available", return_value=False):
            pairs = design_primers("ATCG" * 100, 150, 23)
        assert pairs == []

    def test_returns_empty_on_error(self):
        mock_primer3 = MagicMock()
        mock_primer3.design_primers = MagicMock(side_effect=Exception("Primer3 error"))

        with patch("crisprairs.apis.primer3_api.check_available", return_value=True):
            with patch.dict(sys.modules, {"primer3": mock_primer3}):
                pairs = design_primers("ATCG" * 100, 150, 23)
        assert pairs == []


class TestDefaultParams:
    def test_has_required_keys(self):
        assert "PRIMER_OPT_SIZE" in DEFAULT_PARAMS
        assert "PRIMER_OPT_TM" in DEFAULT_PARAMS
        assert "PRIMER_PRODUCT_SIZE_RANGE" in DEFAULT_PARAMS
