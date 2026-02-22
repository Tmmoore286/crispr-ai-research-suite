"""Tests for the audit log module."""

import json

from crisprairs.rpw.audit import AuditLog


class TestAuditLog:
    def test_set_session_and_log(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        AuditLog.set_session("test-session-1")
        AuditLog.log_event("test_event", key="value")

        path = tmp_path / "test-session-1.jsonl"
        assert path.exists()

        with open(path) as f:
            entry = json.loads(f.readline())
        assert entry["event"] == "test_event"
        assert entry["key"] == "value"
        assert entry["session_id"] == "test-session-1"
        assert "ts" in entry

    def test_read_events(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        AuditLog.set_session("test-session-2")
        AuditLog.log_event("event_a")
        AuditLog.log_event("event_b", detail="info")

        events = AuditLog.read_events("test-session-2")
        assert len(events) == 2
        assert events[0]["event"] == "event_a"
        assert events[1]["detail"] == "info"

    def test_read_events_no_file(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        events = AuditLog.read_events("nonexistent")
        assert events == []

    def test_list_sessions(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        (tmp_path / "sess-a.jsonl").write_text("")
        (tmp_path / "sess-b.jsonl").write_text("")

        sessions = AuditLog.list_sessions()
        assert "sess-a" in sessions
        assert "sess-b" in sessions

    def test_no_session_does_not_error(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        AuditLog._session_id = None
        AuditLog.log_event("ignored")  # should not raise
        assert AuditLog.read_events() == []
