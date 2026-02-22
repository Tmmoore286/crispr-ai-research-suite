"""Feedback collection and summary reporting for session audit trails."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

from crisprairs.rpw.audit import AuditLog

logger = logging.getLogger(__name__)


@dataclass
class _StateTally:
    positive: int = 0
    negative: int = 0


@dataclass
class _FeedbackStats:
    sessions: int = 0
    interactions: int = 0
    positive: int = 0
    negative: int = 0
    safety_blocks: int = 0
    latencies_ms: list[int] = field(default_factory=list)
    by_state: dict[str, _StateTally] = field(default_factory=dict)

    def state_bucket(self, state: str) -> _StateTally:
        if state not in self.by_state:
            self.by_state[state] = _StateTally()
        return self.by_state[state]


class FeedbackCollector:
    """Collects user feedback and computes aggregate quality metrics."""

    @classmethod
    def on_feedback(cls, like_data) -> None:
        """Persist a like/dislike event emitted by Gradio Chatbot."""
        rating = "positive" if bool(getattr(like_data, "liked", False)) else "negative"
        message_index = getattr(like_data, "index", None)
        AuditLog.log_event(
            "user_feedback",
            rating=rating,
            message_index=message_index,
        )
        logger.info("Feedback recorded: %s at index %s", rating, message_index)

    @classmethod
    def aggregate_report(cls, session_ids: list[str] | None = None) -> str:
        """Generate an aggregate report for one or more sessions."""
        ids = session_ids if session_ids is not None else AuditLog.list_sessions()
        stats = cls._build_stats(ids)

        total_feedback = stats.positive + stats.negative
        pct_positive = (
            f"{stats.positive / total_feedback * 100:.0f}%"
            if total_feedback > 0
            else "N/A"
        )
        safety_pct = (
            f"{stats.safety_blocks / stats.interactions * 100:.1f}%"
            if stats.interactions > 0
            else "N/A"
        )
        avg_latency = (
            f"{sum(stats.latencies_ms) / len(stats.latencies_ms) / 1000:.1f}s"
            if stats.latencies_ms
            else "N/A"
        )

        best_state, worst_state = cls._best_and_worst_state(stats.by_state)

        return (
            f"Sessions: {stats.sessions} | "
            f"Interactions: {stats.interactions} | "
            f"Positive: {pct_positive}\n"
            f"Best:  {best_state}\n"
            f"Worst: {worst_state}\n"
            f"Safety blocks: {stats.safety_blocks} ({safety_pct})\n"
            f"Avg response: {avg_latency}"
        )

    @classmethod
    def _build_stats(cls, session_ids: Iterable[str]) -> _FeedbackStats:
        stats = _FeedbackStats(sessions=len(list(session_ids)))
        # Re-materialize IDs because we used len(...) above.
        ids = list(session_ids)

        for sid in ids:
            current_state = "unknown"
            for event in AuditLog.read_events(sid):
                event_type = event.get("event")

                if event_type == "llm_call":
                    stats.interactions += 1
                    latency = event.get("latency_ms")
                    if isinstance(latency, (int, float)):
                        stats.latencies_ms.append(int(latency))
                    continue

                if event_type == "state_transition":
                    current_state = event.get("to", current_state)
                    continue

                if event_type == "safety_block":
                    stats.safety_blocks += 1
                    continue

                if event_type == "user_feedback":
                    rating = event.get("rating")
                    bucket = stats.state_bucket(current_state)
                    if rating == "positive":
                        stats.positive += 1
                        bucket.positive += 1
                    elif rating == "negative":
                        stats.negative += 1
                        bucket.negative += 1

        stats.sessions = len(ids)
        return stats

    @staticmethod
    def _best_and_worst_state(by_state: dict[str, _StateTally]) -> tuple[str, str]:
        best_state = "N/A"
        worst_state = "N/A"
        best_rate = -1.0
        worst_rate = 101.0

        for state, tally in by_state.items():
            total = tally.positive + tally.negative
            if total < 2:
                continue
            rate = tally.positive / total * 100
            if rate > best_rate:
                best_rate = rate
                best_state = f"{state} ({rate:.0f}%)"
            if rate < worst_rate:
                worst_rate = rate
                worst_state = f"{state} ({rate:.0f}%)"

        return best_state, worst_state
