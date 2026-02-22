"""Append-only audit event logging for session-level observability."""

from __future__ import annotations

import contextvars
import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AUDIT_DIR = Path("audit")
AUDIT_DIR.mkdir(exist_ok=True)


@dataclass
class _AuditEntry:
    ts: str
    session_id: str
    event: str
    fields: dict[str, Any]

    def to_json_line(self) -> str:
        body = {"ts": self.ts, "session_id": self.session_id, "event": self.event}
        body.update(self.fields)
        return json.dumps(body, default=str) + "\n"


class AuditLog:
    """Write and read JSONL audit logs grouped by session ID."""

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
        if sid is None or path is None:
            return

        entry = _AuditEntry(
            ts=datetime.now(timezone.utc).isoformat(),
            session_id=sid,
            event=event,
            fields=kwargs,
        )

        try:
            with cls._lock:
                with open(path, "a", encoding="utf-8") as handle:
                    handle.write(entry.to_json_line())
        except Exception as exc:
            logger.error("Audit write error: %s", exc)

    @classmethod
    def read_events(cls, session_id=None):
        """Read decoded audit events for one session."""
        sid = session_id or cls.current_session()
        if sid is None:
            return []

        path = AUDIT_DIR / f"{sid}.jsonl"
        if not path.exists():
            return []

        events = []
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    parsed = _decode_line(line)
                    if parsed is not None:
                        events.append(parsed)
        except Exception as exc:
            logger.error("Audit read error: %s", exc)
            return []

        return events

    @classmethod
    def list_sessions(cls):
        """Return known session IDs with audit logs."""
        return sorted(path.stem for path in AUDIT_DIR.glob("*.jsonl"))


def _decode_line(line: str):
    raw = line.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
