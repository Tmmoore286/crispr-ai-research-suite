"""Tests for the session management module."""

from crisprairs.rpw.sessions import SessionManager


class TestSessionManager:
    def test_save_and_load(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save(
            "s1",
            chat_history=[("Hello", "Hi there")],
            workflow_state="knockout",
            provider="openai",
            model="gpt-4o",
        )

        data = SessionManager.load("s1")
        assert data is not None
        assert data["session_id"] == "s1"
        assert data["workflow_state"] == "knockout"
        assert data["provider"] == "openai"
        assert len(data["chat_history"]) > 0

    def test_save_with_context_dict(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save(
            "s2",
            chat_history=[],
            context_dict={"target_gene": "BRCA1", "species": "human"},
        )

        data = SessionManager.load("s2")
        assert data["context"]["target_gene"] == "BRCA1"

    def test_load_nonexistent(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        assert SessionManager.load("nonexistent") is None

    def test_list_sessions(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save("s-a", chat_history=[])
        SessionManager.save("s-b", chat_history=[])

        sessions = SessionManager.list_sessions()
        ids = [s["session_id"] for s in sessions]
        assert "s-a" in ids
        assert "s-b" in ids

    def test_restore_chat_history(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save("s3", chat_history=[("User msg", "Bot reply")])
        history = SessionManager.restore_chat_history("s3")

        assert len(history) > 0
        assert history[0][0] == "User msg"

    def test_export_markdown(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save("s4", chat_history=[("Hello", "World")])
        md = SessionManager.export_markdown("s4")

        assert "Session Report" in md
        assert "s4" in md

    def test_export_nonexistent(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        assert SessionManager.export_markdown("nope") == ""

    def test_update_existing_session(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save("s5", chat_history=[("A", "B")])
        SessionManager.save("s5", chat_history=[("A", "B"), ("C", "D")])

        data = SessionManager.load("s5")
        assert "created_at" in data
        assert "updated_at" in data
