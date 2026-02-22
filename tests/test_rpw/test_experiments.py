"""Tests for the experiment tracker module."""

import pytest

from crisprairs.rpw.experiments import VALID_RESULT_TYPES, ExperimentTracker


class TestExperimentTracker:
    def test_log_and_get_result(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        ExperimentTracker.log_result(
            "s1",
            "editing_efficiency",
            data={"gene": "BRCA1", "efficiency": 0.45},
        )

        results = ExperimentTracker.get_results("s1")
        assert len(results) == 1
        assert results[0]["result_type"] == "editing_efficiency"
        assert results[0]["data"]["efficiency"] == 0.45

    def test_invalid_result_type(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        with pytest.raises(ValueError, match="Invalid result_type"):
            ExperimentTracker.log_result("s1", "invalid_type")

    def test_multiple_results(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        ExperimentTracker.log_result("s2", "editing_efficiency")
        ExperimentTracker.log_result("s2", "phenotype_confirmed")

        results = ExperimentTracker.get_results("s2")
        assert len(results) == 2

    def test_get_results_no_file(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        assert ExperimentTracker.get_results("nonexistent") == []

    def test_experiment_history_filter(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        ExperimentTracker.log_result(
            "s3", "editing_efficiency",
            data={"gene": "BRCA1", "species": "human"},
        )
        ExperimentTracker.log_result(
            "s4", "editing_efficiency",
            data={"gene": "TP53", "species": "mouse"},
        )

        results = ExperimentTracker.get_experiment_history(gene="BRCA1")
        assert len(results) == 1
        assert results[0]["data"]["gene"] == "BRCA1"

    def test_compare_results(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        ExperimentTracker.log_result("s5", "editing_efficiency", data={"val": 0.5})
        ExperimentTracker.log_result("s6", "editing_efficiency", data={"val": 0.8})

        comparison = ExperimentTracker.compare_results(["s5", "s6"])
        assert len(comparison) == 2

    def test_format_comparison_markdown(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        ExperimentTracker.log_result("s7", "editing_efficiency")
        md = ExperimentTracker.format_comparison_markdown(["s7"])
        assert "Experiment Comparison" in md

    def test_format_empty_comparison(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        md = ExperimentTracker.format_comparison_markdown(["nonexistent"])
        assert "No results" in md

    def test_list_tracked_sessions(self, tmp_path, monkeypatch):
        import crisprairs.rpw.experiments as mod
        monkeypatch.setattr(mod, "EXPERIMENTS_DIR", tmp_path)

        ExperimentTracker.log_result("s8", "editing_efficiency")
        sessions = ExperimentTracker.list_tracked_sessions()
        assert "s8" in sessions

    def test_valid_result_types(self):
        assert "editing_efficiency" in VALID_RESULT_TYPES
        assert "experiment_failed" in VALID_RESULT_TYPES
        assert len(VALID_RESULT_TYPES) == 6
