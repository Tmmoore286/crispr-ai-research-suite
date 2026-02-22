"""Multi-user collaboration: sharing, annotations, and PI review."""

import hashlib
import json
import logging
from datetime import datetime, timezone

from crisprairs.rpw.sessions import SessionManager, SESSIONS_DIR
from crisprairs.rpw.audit import AuditLog

logger = logging.getLogger(__name__)


class Collaboration:
    """Lightweight collaboration layer on top of sessions.

    No authentication — uses name-based identification suitable for
    a lab-internal tool.
    """

    # ---- Sharing ----

    @classmethod
    def share_session(cls, session_id, owner=None):
        """Generate a shareable token for a session."""
        data = SessionManager.load(session_id)
        if data is None:
            return None

        token = hashlib.sha256(session_id.encode()).hexdigest()[:12]

        data.setdefault("shared_with", [])
        data["share_token"] = token
        if owner:
            data["owner"] = owner

        cls._save_raw(session_id, data)

        AuditLog.log_event(
            "session_shared",
            session_id=session_id,
            share_token=token,
            owner=owner or "",
        )
        return token

    @classmethod
    def lookup_by_token(cls, token):
        """Find a session ID by its share token."""
        for p in SESSIONS_DIR.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("share_token") == token:
                    return data.get("session_id", p.stem)
            except Exception:
                continue
        return None

    # ---- Annotations ----

    @classmethod
    def add_annotation(cls, session_id, step_index, comment, author):
        """Add a comment annotation to a specific conversation step."""
        data = SessionManager.load(session_id)
        if data is None:
            return False

        annotations = data.setdefault("annotations", [])
        annotations.append({
            "step_index": step_index,
            "comment": comment,
            "author": author,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        cls._save_raw(session_id, data)

        AuditLog.log_event(
            "annotation_added",
            session_id=session_id,
            step_index=step_index,
            author=author,
        )
        return True

    @classmethod
    def list_annotations(cls, session_id):
        """Return all annotations for a session, sorted by timestamp."""
        data = SessionManager.load(session_id)
        if data is None:
            return []
        annotations = data.get("annotations", [])
        return sorted(annotations, key=lambda a: a.get("timestamp", ""))

    @classmethod
    def get_annotations_for_step(cls, session_id, step_index):
        """Return annotations for a specific conversation step."""
        return [
            a for a in cls.list_annotations(session_id)
            if a.get("step_index") == step_index
        ]

    # ---- PI Review ----

    @classmethod
    def request_pi_review(cls, session_id, requester=None):
        """Mark a session as needing PI sign-off."""
        data = SessionManager.load(session_id)
        if data is None:
            return False

        data["pi_review"] = {
            "status": "pending",
            "requested_by": requester or "",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewer": None,
            "decision": None,
        }

        cls._save_raw(session_id, data)

        AuditLog.log_event(
            "pi_review_requested",
            session_id=session_id,
            requester=requester or "",
        )
        return True

    @classmethod
    def complete_pi_review(cls, session_id, reviewer, decision, comment=None):
        """Complete a PI review with approve/revise/reject decision."""
        data = SessionManager.load(session_id)
        if data is None:
            return False

        review = data.get("pi_review")
        if review is None:
            return False

        review["status"] = "completed"
        review["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        review["reviewer"] = reviewer
        review["decision"] = decision
        if comment:
            review["comment"] = comment

        cls._save_raw(session_id, data)

        AuditLog.log_event(
            "pi_review_completed",
            session_id=session_id,
            reviewer=reviewer,
            decision=decision,
        )
        return True

    @classmethod
    def get_pi_review_status(cls, session_id):
        """Return the PI review record for a session, or None."""
        data = SessionManager.load(session_id)
        if data is None:
            return None
        return data.get("pi_review")

    # ---- Helpers ----

    @classmethod
    def _save_raw(cls, session_id, data):
        """Write session data dict directly to disk."""
        path = SESSIONS_DIR / f"{session_id}.json"
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error("Collaboration save error: %s", e)

    @classmethod
    def format_annotations_markdown(cls, session_id):
        """Format all annotations as a Markdown section for export."""
        annotations = cls.list_annotations(session_id)
        if not annotations:
            return ""
        lines = ["## Annotations", ""]
        for a in annotations:
            step = a.get("step_index", "?")
            author = a.get("author", "Unknown")
            ts = a.get("timestamp", "")
            comment = a.get("comment", "")
            lines.append(f"**Step {step}** — *{author}* ({ts})")
            lines.append(f"> {comment}")
            lines.append("")
        return "\n".join(lines)
