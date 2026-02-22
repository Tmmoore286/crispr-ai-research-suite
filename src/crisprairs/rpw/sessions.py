"""Session layer: save, load, resume, and export sessions."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


class SessionManager:
    """Persists full session state as JSON for resume and export."""

    @classmethod
    def _file_path(cls, session_id):
        return SESSIONS_DIR / f"{session_id}.json"

    @classmethod
    def save(cls, session_id, chat_history, workflow_state=None,
             provider=None, model=None, context_dict=None):
        """Save session state to disk.

        Parameters
        ----------
        context_dict : dict, optional
            Serialized ``SessionContext.to_dict()`` for typed session state.
        """
        path = cls._file_path(session_id)
        now = datetime.now(timezone.utc).isoformat()

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["updated_at"] = now
        else:
            data = {
                "session_id": session_id,
                "created_at": now,
                "updated_at": now,
            }

        # Convert Gradio tuples to serializable chat history
        serializable_history = []
        for item in chat_history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                serializable_history.append({
                    "role": "user" if item[0] else "assistant",
                    "content": item[0] or item[1],
                    "timestamp": now,
                })
                if item[0] and item[1]:
                    serializable_history.append({
                        "role": "assistant",
                        "content": item[1],
                        "timestamp": now,
                    })
            else:
                serializable_history.append({
                    "role": "unknown",
                    "content": str(item),
                    "timestamp": now,
                })

        data["chat_history"] = serializable_history
        if workflow_state is not None:
            data["workflow_state"] = workflow_state
        if provider is not None:
            data["provider"] = provider
        if model is not None:
            data["model"] = model
        if context_dict is not None:
            safe_ctx = {}
            for k, v in context_dict.items():
                try:
                    json.dumps(v, default=str)
                    safe_ctx[k] = v
                except (TypeError, ValueError):
                    safe_ctx[k] = str(v)
            data["context"] = safe_ctx

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error("Session save error: %s", e)

    @classmethod
    def load(cls, session_id):
        """Load session data from disk. Returns dict or None."""
        path = cls._file_path(session_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Session load error: %s", e)
            return None

    @classmethod
    def list_sessions(cls):
        """List all saved session IDs with metadata."""
        sessions = []
        for p in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id", p.stem),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "provider": data.get("provider", ""),
                    "workflow_state": data.get("workflow_state", ""),
                })
            except Exception:
                sessions.append({"session_id": p.stem})
        return sessions

    @classmethod
    def restore_chat_history(cls, session_id):
        """Restore Gradio-compatible chat history tuples from saved session."""
        data = cls.load(session_id)
        if data is None:
            return []
        history = []
        chat = data.get("chat_history", [])
        i = 0
        while i < len(chat):
            msg = chat[i]
            if msg["role"] == "user":
                bot_content = ""
                if i + 1 < len(chat) and chat[i + 1]["role"] == "assistant":
                    bot_content = chat[i + 1]["content"]
                    i += 1
                history.append((msg["content"], bot_content))
            elif msg["role"] == "assistant":
                history.append((None, msg["content"]))
            i += 1
        return history

    @classmethod
    def export_markdown(cls, session_id):
        """Export session as a clean Markdown document."""
        data = cls.load(session_id)
        if data is None:
            return ""

        lines = [
            "# CRISPR AI Research Suite — Session Report",
            "",
            f"**Session ID:** {data.get('session_id', 'N/A')}",
            f"**Created:** {data.get('created_at', 'N/A')}",
            f"**Updated:** {data.get('updated_at', 'N/A')}",
            f"**Provider:** {data.get('provider', 'N/A')}",
            f"**Model:** {data.get('model', 'N/A')}",
            "",
            "---",
            "",
            "## Conversation",
            "",
        ]

        for msg in data.get("chat_history", []):
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            ts = msg.get("timestamp", "")
            lines.append(f"### {role}")
            if ts:
                lines.append(f"*{ts}*")
            lines.append("")
            lines.append(content)
            lines.append("")

        lines.extend([
            "---",
            "",
            "*Exported from CRISPR AI Research Suite.*",
        ])
        return "\n".join(lines)
