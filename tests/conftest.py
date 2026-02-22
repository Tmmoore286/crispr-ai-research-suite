"""Shared fixtures for CRISPR AI Research Suite tests."""

import os
import sys

# Set dummy API keys before any imports that trigger client initialization
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-unit-tests")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-dummy-key-for-unit-tests")
os.environ.setdefault("NCBI_EMAIL", "test@example.com")

import pytest


@pytest.fixture(autouse=True)
def _isolate_data_dirs(tmp_path, monkeypatch):
    """Redirect audit/, sessions/, experiments/ to temp dirs so tests don't pollute the repo."""
    for dirname in ("audit", "sessions", "experiments"):
        d = tmp_path / dirname
        d.mkdir()

    # These will be patched when the RPW modules are imported
    try:
        import crisprairs.rpw.audit as audit_mod
        monkeypatch.setattr(audit_mod, "AUDIT_DIR", tmp_path / "audit")
    except (ImportError, AttributeError):
        pass

    try:
        import crisprairs.rpw.sessions as sessions_mod
        monkeypatch.setattr(sessions_mod, "SESSIONS_DIR", tmp_path / "sessions")
    except (ImportError, AttributeError):
        pass

    try:
        import crisprairs.rpw.experiments as experiments_mod
        monkeypatch.setattr(experiments_mod, "EXPERIMENTS_DIR", tmp_path / "experiments")
    except (ImportError, AttributeError):
        pass
