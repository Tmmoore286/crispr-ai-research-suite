"""Tests for the Gradio app module."""

import pytest
from unittest.mock import patch, MagicMock

gradio = pytest.importorskip("gradio", reason="gradio not installed")

from crisprairs.app import (
    _build_router,
    _new_session_state,
    chat_respond,
    export_protocol,
    export_session,
    new_session,
    build_app,
    WELCOME_MESSAGE,
    MODALITY_MAP,
)


class TestRouter:
    def test_build_router_has_modalities(self):
        router = _build_router()
        modalities = router.modalities
        assert "knockout" in modalities
        assert "base_editing" in modalities
        assert "prime_editing" in modalities
        assert "activation" in modalities
        assert "repression" in modalities
        assert "off_target" in modalities
        assert "troubleshoot" in modalities


class TestModalityMap:
    def test_number_shortcuts(self):
        assert MODALITY_MAP["1"] == "knockout"
        assert MODALITY_MAP["2"] == "base_editing"
        assert MODALITY_MAP["7"] == "troubleshoot"

    def test_name_shortcuts(self):
        assert MODALITY_MAP["knockout"] == "knockout"
        assert MODALITY_MAP["base editing"] == "base_editing"
        assert MODALITY_MAP["crispra"] == "activation"
        assert MODALITY_MAP["crispri"] == "repression"


class TestSessionState:
    def test_new_session_state(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        state = _new_session_state()
        assert "session_id" in state
        assert state["ctx"] is not None
        assert state["runner"] is None
        assert state["started"] is False


class TestChatRespond:
    def test_unrecognized_modality(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state = chat_respond("nonsense", [], None)
        assert len(history) == 1
        assert "didn't recognize" in history[0][1]

    def test_safety_block(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state = chat_respond(
            "I want to edit human embryos for germline modification",
            [], None,
        )
        assert "Safety Notice" in history[0][1]

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_knockout_workflow_start(self, mock_chat, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        import crisprairs.rpw.sessions as smod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)
        monkeypatch.setattr(smod, "SESSIONS_DIR", tmp_path)

        # Starting knockout workflow — the first step (KnockoutTargetInput)
        # has needs_input=True, so it should pause with a prompt
        history, state = chat_respond("1", [], None)

        assert state["started"] is True
        assert state["ctx"].modality == "knockout"
        assert len(history) == 1
        # Should contain the prompt message from KnockoutTargetInput
        assert history[0][1]  # non-empty response

    def test_completed_workflow_message(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        state = _new_session_state()
        state["started"] = True
        # Simulate a done runner
        runner = MagicMock()
        runner.is_done = True
        state["runner"] = runner

        history, state = chat_respond("anything", [], state)
        assert "complete" in history[0][1].lower()


class TestExport:
    def test_export_protocol_no_session(self):
        result = export_protocol(None)
        assert "No active session" in result

    def test_export_protocol_with_state(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        from crisprairs.engine.context import SessionContext
        state = {
            "session_id": "test123",
            "ctx": SessionContext(target_gene="BRCA1", species="human", modality="knockout"),
        }
        result = export_protocol(state)
        assert "BRCA1" in result
        assert "Protocol" in result

    def test_export_session_no_state(self):
        result = export_session(None)
        assert "No active session" in result


class TestNewSession:
    def test_new_session_resets(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state, msg = new_session(None)
        assert history == []
        assert state is not None
        assert state["started"] is False


class TestBuildApp:
    def test_build_app_returns_blocks(self):
        app = build_app()
        assert app is not None
