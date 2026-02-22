"""Collaboration primitives for sharing, annotations, and PI review."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from crisprairs.rpw.audit import AuditLog
from crisprairs.rpw.sessions import SESSIONS_DIR, SessionManager

logger = logging.getLogger(__name__)


@dataclass
class _ReviewRecord:
    status: str
    requested_by: str
    requested_at: str
    reviewed_at: str | None = None
    reviewer: str | None = None
    decision: str | None = None
    comment: str | None = None


class Collaboration:
    """Collaboration API on top of persisted session data."""

    @classmethod
    def share_session(cls, session_id, owner=None):
        """Generate and persist a short share token for a session."""
        doc = SessionManager.load(session_id)
        if doc is None:
            return None

        token = cls._share_token(session_id)
        doc.setdefault("shared_with", [])
        doc["share_token"] = token
        if owner:
            doc["owner"] = owner

        cls._persist_session(session_id, doc)
        AuditLog.log_event(
            "session_shared",
            session_id=session_id,
            share_token=token,
            owner=owner or "",
        )
        return token

    @classmethod
    def lookup_by_token(cls, token):
        """Resolve a share token to session ID if present."""
        for session_path in SESSIONS_DIR.glob("*.json"):
            data = cls._read_json(session_path)
            if not data:
                continue
            if data.get("share_token") == token:
                return data.get("session_id", session_path.stem)
        return None

    @classmethod
    def add_annotation(cls, session_id, step_index, comment, author):
        """Attach a comment to a specific workflow/chat step."""
        doc = SessionManager.load(session_id)
        if doc is None:
            return False

        note = {
            "step_index": step_index,
            "comment": comment,
            "author": author,
            "timestamp": cls._now_iso(),
        }
        doc.setdefault("annotations", []).append(note)

        cls._persist_session(session_id, doc)
        AuditLog.log_event(
            "annotation_added",
            session_id=session_id,
            step_index=step_index,
            author=author,
        )
        return True

    @classmethod
    def list_annotations(cls, session_id):
        """Return all annotations ordered by timestamp."""
        doc = SessionManager.load(session_id)
        if doc is None:
            return []
        annotations = doc.get("annotations", [])
        return sorted(annotations, key=lambda a: a.get("timestamp", ""))

    @classmethod
    def get_annotations_for_step(cls, session_id, step_index):
        """Return only annotations matching a step index."""
        return [
            item
            for item in cls.list_annotations(session_id)
            if item.get("step_index") == step_index
        ]

    @classmethod
    def request_pi_review(cls, session_id, requester=None):
        """Mark a session as pending PI review."""
        doc = SessionManager.load(session_id)
        if doc is None:
            return False

        review = _ReviewRecord(
            status="pending",
            requested_by=requester or "",
            requested_at=cls._now_iso(),
        )
        doc["pi_review"] = review.__dict__

        cls._persist_session(session_id, doc)
        AuditLog.log_event(
            "pi_review_requested",
            session_id=session_id,
            requester=requester or "",
        )
        return True

    @classmethod
    def complete_pi_review(cls, session_id, reviewer, decision, comment=None):
        """Close an existing PI review record with a decision."""
        doc = SessionManager.load(session_id)
        if doc is None:
            return False

        review = doc.get("pi_review")
        if not isinstance(review, dict):
            return False

        review["status"] = "completed"
        review["reviewed_at"] = cls._now_iso()
        review["reviewer"] = reviewer
        review["decision"] = decision
        if comment:
            review["comment"] = comment

        cls._persist_session(session_id, doc)
        AuditLog.log_event(
            "pi_review_completed",
            session_id=session_id,
            reviewer=reviewer,
            decision=decision,
        )
        return True

    @classmethod
    def get_pi_review_status(cls, session_id):
        """Fetch PI review metadata for a session if present."""
        doc = SessionManager.load(session_id)
        if doc is None:
            return None
        return doc.get("pi_review")

    @classmethod
    def format_annotations_markdown(cls, session_id):
        """Render all annotations in markdown for report export."""
        annotations = cls.list_annotations(session_id)
        if not annotations:
            return ""

        lines = ["## Annotations", ""]
        for item in annotations:
            step = item.get("step_index", "?")
            author = item.get("author", "Unknown")
            ts = item.get("timestamp", "")
            comment = item.get("comment", "")
            lines.append(f"**Step {step}** — *{author}* ({ts})")
            lines.append(f"> {comment}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _share_token(session_id: str) -> str:
        digest = hashlib.blake2s(session_id.encode("utf-8"), digest_size=16).hexdigest()
        return digest[:12]

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _persist_session(cls, session_id: str, data: dict[str, Any]) -> None:
        path = SESSIONS_DIR / f"{session_id}.json"
        data["updated_at"] = cls._now_iso()
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, default=str)
        except Exception as exc:
            logger.error("Collaboration save error: %s", exc)

    @staticmethod
    def _read_json(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None
