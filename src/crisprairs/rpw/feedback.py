"""Feedback hook: thumbs up/down collection and aggregate metrics."""

import logging
from collections import defaultdict

from crisprairs.rpw.audit import AuditLog

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """Collects user feedback via Gradio's chatbot.like() and writes to audit log."""

    @classmethod
    def on_feedback(cls, like_data):
        """Gradio chatbot.like() event handler.

        like_data is a gr.LikeData with .liked (bool) and .index (tuple).
        """
        rating = "positive" if like_data.liked else "negative"
        AuditLog.log_event(
            "user_feedback",
            rating=rating,
            message_index=like_data.index,
        )
        logger.info("Feedback recorded: %s at index %s", rating, like_data.index)

    @classmethod
    def aggregate_report(cls, session_ids=None):
        """Generate aggregate feedback report across sessions."""
        if session_ids is None:
            session_ids = AuditLog.list_sessions()

        total_sessions = len(session_ids)
        total_interactions = 0
        positive = 0
        negative = 0
        safety_blocks = 0
        latencies = []
        state_feedback = defaultdict(lambda: {"positive": 0, "negative": 0})

        for sid in session_ids:
            events = AuditLog.read_events(sid)
            current_state = "unknown"
            for ev in events:
                event_type = ev.get("event")
                if event_type == "llm_call":
                    total_interactions += 1
                    ms = ev.get("latency_ms")
                    if ms is not None:
                        latencies.append(ms)
                elif event_type == "state_transition":
                    current_state = ev.get("to", current_state)
                elif event_type == "safety_block":
                    safety_blocks += 1
                elif event_type == "user_feedback":
                    rating = ev.get("rating")
                    if rating == "positive":
                        positive += 1
                        state_feedback[current_state]["positive"] += 1
                    elif rating == "negative":
                        negative += 1
                        state_feedback[current_state]["negative"] += 1

        total_feedback = positive + negative
        pct_positive = (
            f"{positive / total_feedback * 100:.0f}%"
            if total_feedback > 0
            else "N/A"
        )
        safety_pct = (
            f"{safety_blocks / total_interactions * 100:.1f}%"
            if total_interactions > 0
            else "N/A"
        )
        avg_latency = (
            f"{sum(latencies) / len(latencies) / 1000:.1f}s"
            if latencies
            else "N/A"
        )

        best_state = worst_state = "N/A"
        best_rate = -1
        worst_rate = 101
        for state, counts in state_feedback.items():
            total = counts["positive"] + counts["negative"]
            if total < 2:
                continue
            rate = counts["positive"] / total * 100
            if rate > best_rate:
                best_rate = rate
                best_state = f"{state} ({rate:.0f}%)"
            if rate < worst_rate:
                worst_rate = rate
                worst_state = f"{state} ({rate:.0f}%)"

        report = (
            f"Sessions: {total_sessions} | "
            f"Interactions: {total_interactions} | "
            f"Positive: {pct_positive}\n"
            f"Best:  {best_state}\n"
            f"Worst: {worst_state}\n"
            f"Safety blocks: {safety_blocks} ({safety_pct})\n"
            f"Avg response: {avg_latency}"
        )
        return report
