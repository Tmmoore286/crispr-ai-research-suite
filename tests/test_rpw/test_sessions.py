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

    def test_save_dict_history_roundtrip(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        dict_history = [
            {"role": "assistant", "content": "Welcome"},
            {"role": "user", "content": "Design TP53 knockout"},
            {"role": "assistant", "content": "Please provide species."},
        ]

        SessionManager.save("s6", chat_history=dict_history)
        data = SessionManager.load("s6")

        assert data is not None
        assert data["chat_history"][0]["role"] == "assistant"
        assert data["chat_history"][1]["role"] == "user"
        assert all(msg["role"] != "unknown" for msg in data["chat_history"])

    def test_restore_chat_history_from_dict_messages(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        dict_history = [
            {"role": "assistant", "content": "Welcome"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Next"},
        ]
        SessionManager.save("s7", chat_history=dict_history)
        history = SessionManager.restore_chat_history("s7")

        assert history == [(None, "Welcome"), ("Hello", "Hi"), ("Next", "")]

    def test_export_markdown_preserves_roles_from_dict_history(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        dict_history = [
            {"role": "assistant", "content": "Welcome"},
            {"role": "user", "content": "Run knockout"},
        ]
        SessionManager.save("s8", chat_history=dict_history)
        md = SessionManager.export_markdown("s8")

        assert "### Assistant" in md
        assert "### User" in md
        assert "### Unknown" not in md

    def test_mixed_tuple_and_dict_history_compatibility(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        mixed = [
            ("Legacy user", "Legacy bot"),
            {"role": "user", "content": "Modern user"},
            {"role": "assistant", "content": "Modern bot"},
        ]
        SessionManager.save("s9", chat_history=mixed)
        data = SessionManager.load("s9")

        assert data is not None
        roles = [m["role"] for m in data["chat_history"]]
        assert roles[:2] == ["user", "assistant"]
        assert roles[-2:] == ["user", "assistant"]

    def test_export_markdown_includes_evidence_trace(self, tmp_path, monkeypatch):
        import crisprairs.rpw.sessions as mod
        monkeypatch.setattr(mod, "SESSIONS_DIR", tmp_path)

        SessionManager.save(
            "s10",
            chat_history=[{"role": "assistant", "content": "hello"}],
            context_dict={
                "literature_query": "(CRISPR) AND (TP53)",
                "literature_hits": [{"pmid": "123", "title": "CRISPR TP53 paper"}],
                "evidence_gaps": ["Low hit count"],
                "evidence_metrics": {"papers_found": 1},
            },
        )
        md = SessionManager.export_markdown("s10")

        assert "## Evidence Trace" in md
        assert "PMID 123" in md
        assert "Evidence Gaps" in md
