"""Experiment tracking for wet-lab results tied to session IDs."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EXPERIMENTS_DIR = Path("experiments")
EXPERIMENTS_DIR.mkdir(exist_ok=True)

VALID_RESULT_TYPES = (
    "editing_efficiency",
    "off_target_detected",
    "phenotype_confirmed",
    "experiment_failed",
    "expression_change",
    "cell_viability",
)


@dataclass
class _ResultEntry:
    result_type: str
    timestamp: str
    data: dict[str, Any]


class ExperimentTracker:
    """Persist and query structured experiment outcomes."""

    @classmethod
    def _file_path(cls, session_id):
        return EXPERIMENTS_DIR / f"{session_id}.json"

    @classmethod
    def log_result(cls, session_id, result_type, data=None):
        """Append an experiment result for the given session."""
        cls._validate_result_type(result_type)

        now = cls._utc_now()
        payload = cls._load_doc(session_id) or {
            "session_id": session_id,
            "created_at": now,
            "results": [],
        }

        entry = _ResultEntry(
            result_type=result_type,
            timestamp=now,
            data=dict(data or {}),
        )
        payload.setdefault("results", []).append(entry.__dict__)
        payload["updated_at"] = now

        cls._write_doc(session_id, payload)
        cls._log_audit(session_id, result_type)
        logger.info("Result logged: %s for session %s", result_type, session_id)

    @classmethod
    def get_results(cls, session_id):
        """Return all result entries for a session."""
        doc = cls._load_doc(session_id)
        if not doc:
            return []
        return doc.get("results", [])

    @classmethod
    def get_experiment_history(cls, gene=None, species=None):
        """Search all tracked sessions with optional gene/species filters."""
        matches = []
        for path in sorted(EXPERIMENTS_DIR.glob("*.json")):
            doc = cls._load_doc_from_path(path)
            if not doc:
                continue

            for result in doc.get("results", []):
                data = result.get("data", {})
                if not cls._matches_filter(data, gene=gene, species=species):
                    continue
                matches.append(
                    {
                        "session_id": doc.get("session_id", path.stem),
                        "result_type": result.get("result_type", ""),
                        "timestamp": result.get("timestamp", ""),
                        "data": data,
                    }
                )
        return matches

    @classmethod
    def compare_results(cls, session_ids):
        """Flatten results from multiple sessions into one comparable list."""
        rows = []
        for sid in session_ids:
            for result in cls.get_results(sid):
                row = {
                    "session_id": sid,
                    "result_type": result.get("result_type", ""),
                    "timestamp": result.get("timestamp", ""),
                }
                row.update(result.get("data", {}))
                rows.append(row)
        return rows

    @classmethod
    def format_comparison_markdown(cls, session_ids):
        """Render side-by-side comparison rows as markdown table."""
        rows = cls.compare_results(session_ids)
        if not rows:
            return "*No results to compare.*"

        reserved = ["session_id", "result_type", "timestamp"]
        dynamic = sorted({k for row in rows for k in row.keys()} - set(reserved))
        headers = reserved + dynamic

        lines = ["## Experiment Comparison", ""]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in rows:
            values = [str(row.get(key, "")) for key in headers]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)

    @classmethod
    def list_tracked_sessions(cls):
        """List session IDs that have experiment result files."""
        return sorted(path.stem for path in EXPERIMENTS_DIR.glob("*.json"))

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_result_type(result_type: str) -> None:
        if result_type not in VALID_RESULT_TYPES:
            raise ValueError(
                f"Invalid result_type '{result_type}'. "
                f"Must be one of: {', '.join(VALID_RESULT_TYPES)}"
            )

    @classmethod
    def _load_doc(cls, session_id):
        return cls._load_doc_from_path(cls._file_path(session_id))

    @staticmethod
    def _load_doc_from_path(path: Path):
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return None

    @classmethod
    def _write_doc(cls, session_id, data):
        path = cls._file_path(session_id)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, default=str)

    @staticmethod
    def _matches_filter(data: dict[str, Any], gene=None, species=None) -> bool:
        gene_match = gene is None or str(data.get("gene", "")).lower() == str(gene).lower()
        species_match = (
            species is None or str(data.get("species", "")).lower() == str(species).lower()
        )
        return gene_match and species_match

    @staticmethod
    def _log_audit(session_id: str, result_type: str) -> None:
        try:
            from crisprairs.rpw.audit import AuditLog

            AuditLog.log_event(
                "experiment_result_logged",
                session_id=session_id,
                result_type=result_type,
            )
        except Exception:
            pass
