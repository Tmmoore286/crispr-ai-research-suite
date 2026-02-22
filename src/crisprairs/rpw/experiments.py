"""Experiment tracker: log wet-lab results and compare across sessions."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

EXPERIMENTS_DIR = Path("experiments")
EXPERIMENTS_DIR.mkdir(exist_ok=True)

# Valid result types for structured logging
VALID_RESULT_TYPES = (
    "editing_efficiency",
    "off_target_detected",
    "phenotype_confirmed",
    "experiment_failed",
    "expression_change",
    "cell_viability",
)


class ExperimentTracker:
    """Tracks wet-lab experiment results linked to sessions."""

    @classmethod
    def _file_path(cls, session_id):
        return EXPERIMENTS_DIR / f"{session_id}.json"

    @classmethod
    def log_result(cls, session_id, result_type, data=None):
        """Log a structured experimental result for a session.

        Args:
            session_id: The session this result belongs to.
            result_type: One of VALID_RESULT_TYPES.
            data: Dict with result details (efficiency %, cell line, method, etc.)
        """
        if result_type not in VALID_RESULT_TYPES:
            raise ValueError(
                f"Invalid result_type '{result_type}'. "
                f"Must be one of: {', '.join(VALID_RESULT_TYPES)}"
            )

        path = cls._file_path(session_id)
        now = datetime.now(timezone.utc).isoformat()

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                doc = json.load(f)
        else:
            doc = {
                "session_id": session_id,
                "created_at": now,
                "results": [],
            }

        entry = {
            "result_type": result_type,
            "timestamp": now,
            "data": data or {},
        }
        doc["results"].append(entry)
        doc["updated_at"] = now

        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, default=str)

        try:
            from crisprairs.rpw.audit import AuditLog
            AuditLog.log_event(
                "experiment_result_logged",
                session_id=session_id,
                result_type=result_type,
            )
        except Exception:
            pass

        logger.info("Result logged: %s for session %s", result_type, session_id)

    @classmethod
    def get_results(cls, session_id):
        """Get all logged results for a session."""
        path = cls._file_path(session_id)
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        return doc.get("results", [])

    @classmethod
    def get_experiment_history(cls, gene=None, species=None):
        """Find all experiments, optionally filtered by gene and/or species."""
        matches = []
        for p in sorted(EXPERIMENTS_DIR.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                for result in doc.get("results", []):
                    data = result.get("data", {})
                    gene_match = (
                        gene is None
                        or data.get("gene", "").lower() == gene.lower()
                    )
                    species_match = (
                        species is None
                        or data.get("species", "").lower() == species.lower()
                    )
                    if gene_match and species_match:
                        matches.append({
                            "session_id": doc["session_id"],
                            "result_type": result["result_type"],
                            "timestamp": result["timestamp"],
                            "data": data,
                        })
            except (json.JSONDecodeError, KeyError):
                continue
        return matches

    @classmethod
    def compare_results(cls, session_ids):
        """Compare results across multiple sessions side-by-side."""
        comparison = []
        for sid in session_ids:
            results = cls.get_results(sid)
            for result in results:
                comparison.append({
                    "session_id": sid,
                    "result_type": result["result_type"],
                    "timestamp": result["timestamp"],
                    **result.get("data", {}),
                })
        return comparison

    @classmethod
    def format_comparison_markdown(cls, session_ids):
        """Format a comparison table as Markdown."""
        rows = cls.compare_results(session_ids)
        if not rows:
            return "*No results to compare.*"

        all_keys = set()
        for row in rows:
            all_keys.update(row.keys())
        priority = ["session_id", "result_type", "timestamp"]
        other_keys = sorted(all_keys - set(priority))
        headers = priority + other_keys

        lines = ["## Experiment Comparison", ""]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            vals = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(vals) + " |")

        return "\n".join(lines)

    @classmethod
    def list_tracked_sessions(cls):
        """List all session IDs that have experiment results."""
        return sorted(p.stem for p in EXPERIMENTS_DIR.glob("*.json"))
