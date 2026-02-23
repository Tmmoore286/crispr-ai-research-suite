"""Session persistence helpers for chat history and workflow context."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


class SessionManager:
    """Read/write session documents from JSON files."""

    @classmethod
    def _file_path(cls, session_id):
        return SESSIONS_DIR / f"{session_id}.json"

    @classmethod
    def save(
        cls,
        session_id,
        chat_history,
        workflow_state=None,
        provider=None,
        model=None,
        context_dict=None,
    ):
        """Persist session content and metadata to disk."""
        now = _utc_now()
        payload = cls.load(session_id) or {
            "session_id": session_id,
            "created_at": now,
        }
        payload["updated_at"] = now
        payload["chat_history"] = _normalize_chat_history(chat_history, default_ts=now)

        if workflow_state is not None:
            payload["workflow_state"] = workflow_state
        if provider is not None:
            payload["provider"] = provider
        if model is not None:
            payload["model"] = model
        if context_dict is not None:
            payload["context"] = _json_safe_context(context_dict)

        try:
            with open(cls._file_path(session_id), "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, default=str)
        except Exception as exc:
            logger.error("Session save error: %s", exc)

    @classmethod
    def load(cls, session_id):
        """Load one session payload, returning None if unavailable."""
        path = cls._file_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.error("Session load error: %s", exc)
            return None

    @classmethod
    def list_sessions(cls):
        """Return lightweight metadata rows for all saved sessions."""
        rows = []
        for path in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
            data = cls._load_or_none(path)
            if data is None:
                rows.append({"session_id": path.stem})
                continue
            rows.append(
                {
                    "session_id": data.get("session_id", path.stem),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "provider": data.get("provider", ""),
                    "workflow_state": data.get("workflow_state", ""),
                }
            )
        return rows

    @classmethod
    def restore_chat_history(cls, session_id):
        """Convert saved message list into legacy Gradio tuple history."""
        doc = cls.load(session_id)
        if doc is None:
            return []

        output = []
        messages = doc.get("chat_history", [])
        idx = 0
        while idx < len(messages):
            msg = messages[idx]
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "user":
                assistant_reply = ""
                if idx + 1 < len(messages) and messages[idx + 1].get("role") == "assistant":
                    assistant_reply = messages[idx + 1].get("content", "")
                    idx += 1
                output.append((content, assistant_reply))
            elif role == "assistant":
                output.append((None, content))
            idx += 1
        return output

    @classmethod
    def export_markdown(cls, session_id):
        """Render a session export report in markdown."""
        doc = cls.load(session_id)
        if doc is None:
            return ""

        lines = [
            "# CRISPR AI Research Suite — Session Report",
            "",
            f"**Session ID:** {doc.get('session_id', 'N/A')}",
            f"**Created:** {doc.get('created_at', 'N/A')}",
            f"**Updated:** {doc.get('updated_at', 'N/A')}",
            f"**Provider:** {doc.get('provider', 'N/A')}",
            f"**Model:** {doc.get('model', 'N/A')}",
            "",
            "---",
            "",
            "## Conversation",
            "",
        ]

        for message in doc.get("chat_history", []):
            role = str(message.get("role", "unknown")).capitalize()
            content = str(message.get("content", ""))
            ts = message.get("timestamp", "")
            lines.append(f"### {role}")
            if ts:
                lines.append(f"*{ts}*")
            lines.append("")
            lines.append(content)
            lines.append("")

        context = doc.get("context", {}) if isinstance(doc.get("context"), dict) else {}
        lines.extend(_evidence_markdown_section(context))
        lines.extend(["---", "", "*Exported from CRISPR AI Research Suite.*"])
        return "\n".join(lines)

    @staticmethod
    def _load_or_none(path: Path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe_context(context_dict: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in context_dict.items():
        try:
            json.dumps(value, default=str)
            safe[key] = value
        except (TypeError, ValueError):
            safe[key] = str(value)
    return safe


def _normalize_chat_history(chat_history, default_ts: str) -> list[dict[str, Any]]:
    """Normalize mixed history formats to role/content/timestamp dictionaries."""
    normalized: list[dict[str, Any]] = []

    for item in chat_history:
        if isinstance(item, dict):
            role = str(item.get("role", "unknown")).strip().lower()
            if role not in {"user", "assistant", "system"}:
                role = "unknown"
            normalized.append(
                {
                    "role": role,
                    "content": str(item.get("content", "")),
                    "timestamp": item.get("timestamp", default_ts),
                }
            )
            continue

        if isinstance(item, (list, tuple)) and len(item) == 2:
            user_text, assistant_text = item
            normalized.append(
                {
                    "role": "user" if user_text else "assistant",
                    "content": user_text or assistant_text,
                    "timestamp": default_ts,
                }
            )
            if user_text and assistant_text:
                normalized.append(
                    {
                        "role": "assistant",
                        "content": assistant_text,
                        "timestamp": default_ts,
                    }
                )
            continue

        normalized.append(
            {
                "role": "unknown",
                "content": str(item),
                "timestamp": default_ts,
            }
        )

    return normalized


def _evidence_markdown_section(context: dict[str, Any]) -> list[str]:
    query = str(context.get("literature_query", "") or "")
    hits = context.get("literature_hits", []) or []
    gaps = context.get("evidence_gaps", []) or []
    metrics = context.get("evidence_metrics", {}) or {}

    if not query and not hits and not gaps and not metrics:
        return []

    lines = ["## Evidence Trace", ""]
    if query:
        lines.extend([f"**Query:** `{query}`", ""])

    if hits:
        lines.append("### Top Evidence Hits")
        for hit in hits[:8]:
            pmid = hit.get("pmid", "N/A")
            title = str(hit.get("title", "")).replace("\n", " ")
            lines.append(f"- PMID {pmid}: {title}")
        lines.append("")

    if gaps:
        lines.append("### Evidence Gaps")
        for gap in gaps:
            lines.append(f"- {gap}")
        lines.append("")

    if metrics:
        lines.append("### Evidence Metrics")
        for key in sorted(metrics):
            lines.append(f"- **{key}:** {metrics[key]}")
        lines.append("")

    return lines
