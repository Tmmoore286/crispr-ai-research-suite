"""Structured audit log: append-only JSONL per session."""

import contextvars
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

AUDIT_DIR = Path("audit")
AUDIT_DIR.mkdir(exist_ok=True)


class AuditLog:
    """Append-only JSONL audit logger, one file per session."""

    _session_id = contextvars.ContextVar("audit_session_id", default=None)
    _lock = threading.Lock()

    @classmethod
    def set_session(cls, session_id):
        cls._session_id.set(session_id)

    @classmethod
    def current_session(cls):
        return cls._session_id.get()

    @classmethod
    def _file_path(cls, session_id=None):
        sid = session_id or cls.current_session()
        if sid is None:
            return None
        return AUDIT_DIR / f"{sid}.jsonl"

    @classmethod
    def log_event(cls, event, session_id=None, **kwargs):
        sid = session_id or cls.current_session()
        path = cls._file_path(sid)
        if path is None:
            return
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": sid,
            "event": event,
        }
        entry.update(kwargs)
        line = json.dumps(entry, default=str) + "\n"
        try:
            with cls._lock:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as e:
            logger.error("Audit write error: %s", e)

    @classmethod
    def read_events(cls, session_id=None):
        """Read all events for a session (or current session)."""
        sid = session_id or cls.current_session()
        if sid is None:
            return []
        path = AUDIT_DIR / f"{sid}.jsonl"
        if not path.exists():
            return []
        events = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events

    @classmethod
    def list_sessions(cls):
        """List all session IDs that have audit logs."""
        return sorted(p.stem for p in AUDIT_DIR.glob("*.jsonl"))
