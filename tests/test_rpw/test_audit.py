"""Tests for the audit log module."""

import json
import threading

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

        AuditLog.set_session(None)
        AuditLog.log_event("ignored")  # should not raise
        assert AuditLog.read_events() == []

    def test_log_event_with_explicit_session_id(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        AuditLog.set_session(None)
        AuditLog.log_event("explicit_event", session_id="sess-explicit", key="value")

        path = tmp_path / "sess-explicit.jsonl"
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            entry = json.loads(f.readline())

        assert entry["session_id"] == "sess-explicit"
        assert entry["event"] == "explicit_event"
        assert entry["key"] == "value"

    def test_concurrent_sessions_do_not_cross_contaminate(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as mod
        monkeypatch.setattr(mod, "AUDIT_DIR", tmp_path)

        def _writer(session_id, event_name):
            AuditLog.set_session(session_id)
            AuditLog.log_event(event_name)

        t1 = threading.Thread(target=_writer, args=("sess-1", "event_1"))
        t2 = threading.Thread(target=_writer, args=("sess-2", "event_2"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        events_1 = AuditLog.read_events("sess-1")
        events_2 = AuditLog.read_events("sess-2")

        assert len(events_1) == 1
        assert len(events_2) == 1
        assert events_1[0]["session_id"] == "sess-1"
        assert events_1[0]["event"] == "event_1"
        assert events_2[0]["session_id"] == "sess-2"
        assert events_2[0]["event"] == "event_2"
