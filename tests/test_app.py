"""Tests for the Gradio app module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

if sys.version_info < (3, 10):
    pytest.skip("Gradio requires Python 3.10+", allow_module_level=True)

from crisprairs.app import (
    MODALITY_MAP,
    _build_router,
    _new_session_state,
    build_app,
    chat_respond,
    export_protocol,
    export_protocol_with_file,
    export_session,
    export_session_with_file,
    new_session,
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
        assert len(history) == 2  # user + assistant
        assert history[0]["role"] == "user"
        assert "didn't recognize" in history[1]["content"]

    def test_safety_block(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state = chat_respond(
            "I want to edit human embryos for germline modification",
            [], None,
        )
        assert len(history) == 2  # user + assistant
        assert "Safety Notice" in history[1]["content"]

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
        assert len(history) == 2  # user + assistant
        # Should contain the prompt message from KnockoutTargetInput
        assert history[1]["content"]  # non-empty response

    def test_accepts_gradio_message_parts_history(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state = chat_respond(
            "7",
            [
                {
                    "role": "assistant",
                    "metadata": None,
                    "content": [{"type": "text", "text": "Welcome"}],
                    "options": None,
                }
            ],
            None,
        )

        assert state["started"] is True
        assert state["ctx"].modality == "troubleshoot"
        assert history[-2]["role"] == "user"
        assert history[-2]["content"] == "7"
        assert history[-1]["role"] == "assistant"

    def test_troubleshoot_entry_prompt_not_duplicated(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state = chat_respond("7", [], None)
        assert state["started"] is True
        assert state["ctx"].modality == "troubleshoot"
        assert history[-1]["content"].count("Troubleshooting intake") == 1

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
        assert "complete" in history[1]["content"].lower()


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

    def test_export_protocol_with_file_writes_markdown(self, tmp_path, monkeypatch):
        import crisprairs.app as appmod
        from crisprairs.engine.context import SessionContext

        monkeypatch.setattr(appmod, "EXPORTS_DIR", tmp_path)
        state = {
            "session_id": "sess123",
            "ctx": SessionContext(target_gene="BRCA1", species="human", modality="knockout"),
        }

        markdown, file_path = export_protocol_with_file(state)
        assert "BRCA1" in markdown
        assert file_path is not None
        out_path = tmp_path / Path(file_path).name
        assert out_path.exists()
        assert "BRCA1" in out_path.read_text(encoding="utf-8")

    def test_export_session_with_file_writes_markdown(self, tmp_path, monkeypatch):
        import crisprairs.app as appmod
        import crisprairs.rpw.sessions as smod

        monkeypatch.setattr(appmod, "EXPORTS_DIR", tmp_path / "exports")
        monkeypatch.setattr(smod, "SESSIONS_DIR", tmp_path / "sessions")
        smod.SESSIONS_DIR.mkdir(exist_ok=True)

        smod.SessionManager.save(
            "sessabc",
            chat_history=[
                {"role": "assistant", "content": "hello"},
                {"role": "user", "content": "test"},
            ],
            workflow_state="troubleshoot",
        )
        state = {"session_id": "sessabc", "ctx": object()}

        markdown, file_path = export_session_with_file(state)
        assert "Session Report" in markdown
        assert file_path is not None
        out_path = Path(file_path)
        assert out_path.exists()
        text = out_path.read_text(encoding="utf-8")
        assert "Session Report" in text
        assert "hello" in text


class TestNewSession:
    def test_new_session_resets(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        history, state, msg = new_session(None)
        assert len(history) == 1
        assert history[0]["role"] == "assistant"
        assert "Welcome to CRISPR AI Research Suite" in history[0]["content"]
        assert state is not None
        assert state["started"] is False
        assert msg == ""


class TestBuildApp:
    def test_build_app_returns_blocks(self):
        app = build_app()
        assert app is not None
