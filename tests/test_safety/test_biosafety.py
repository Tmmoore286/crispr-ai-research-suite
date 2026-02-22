"""Tests for safety/biosafety.py — biosafety screening checks."""

from crisprairs.safety.biosafety import (
    check_biosafety,
    has_biosafety_concerns,
    format_biosafety_warnings,
    BiosafetyFlag,
)


class TestGermlineDetection:
    def test_detects_germline_keyword(self):
        flags = check_biosafety("We plan to do human germline editing on embryos")
        assert any(f.category == "germline" for f in flags)

    def test_detects_human_embryo(self):
        flags = check_biosafety("CRISPR editing of human embryo at 2-cell stage")
        assert any(f.trigger == "human embryo" for f in flags)

    def test_detects_zygote_editing(self):
        flags = check_biosafety("Zygote editing with Cas9")
        assert any(f.trigger == "zygote editing" for f in flags)

    def test_case_insensitive(self):
        flags = check_biosafety("HUMAN GERMLINE editing")
        assert any(f.category == "germline" for f in flags)

    def test_no_false_positive_on_somatic(self):
        flags = check_biosafety("Somatic cell editing of T cells with SpCas9")
        germline_flags = [f for f in flags if f.category == "germline"]
        assert len(germline_flags) == 0


class TestSelectAgentDetection:
    def test_detects_anthrax(self):
        flags = check_biosafety("Targeting virulence genes in Bacillus anthracis")
        assert any(f.category == "select_agent" for f in flags)

    def test_detects_ebola(self):
        flags = check_biosafety("Working with ebola virus glycoprotein")
        assert any(f.trigger == "ebola virus" for f in flags)

    def test_detects_yersinia(self):
        flags = check_biosafety("Editing yersinia pestis for attenuation")
        assert any(f.category == "select_agent" for f in flags)

    def test_no_false_positive_on_ecoli(self):
        flags = check_biosafety("Editing E. coli K-12 strain")
        agent_flags = [f for f in flags if f.category == "select_agent"]
        assert len(agent_flags) == 0


class TestDualUseDetection:
    def test_detects_gain_of_function(self):
        flags = check_biosafety("Investigating gain of function mutations")
        assert any(f.category == "dual_use" for f in flags)

    def test_detects_enhance_transmissibility(self):
        flags = check_biosafety("Mutations that enhance transmissibility")
        assert any(f.category == "dual_use" for f in flags)

    def test_no_false_positive_on_normal_research(self):
        flags = check_biosafety("Knockout of TP53 in HEK293T cells")
        durc_flags = [f for f in flags if f.category == "dual_use"]
        assert len(durc_flags) == 0


class TestHasBiosafetyConcerns:
    def test_returns_true_for_flagged(self):
        assert has_biosafety_concerns("human germline editing") is True

    def test_returns_false_for_clean(self):
        assert has_biosafety_concerns("knockout TP53 in mouse") is False


class TestFormatWarnings:
    def test_empty_for_no_flags(self):
        assert format_biosafety_warnings([]) == ""

    def test_includes_category(self):
        flags = [BiosafetyFlag("germline", "human embryo", "Concern about embryo editing")]
        msg = format_biosafety_warnings(flags)
        assert "GERMLINE" in msg
        assert "Biosafety Review Required" in msg
        assert "Institutional Biosafety Committee" in msg

    def test_multiple_flags(self):
        flags = check_biosafety("Human germline editing of ebola virus")
        msg = format_biosafety_warnings(flags)
        assert "GERMLINE" in msg
        assert "SELECT_AGENT" in msg
