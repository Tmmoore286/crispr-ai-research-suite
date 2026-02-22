"""Tests for the feedback collector module."""

import json
from unittest.mock import MagicMock, patch

from crisprairs.rpw.feedback import FeedbackCollector


class TestFeedbackCollector:
    @patch("crisprairs.rpw.feedback.AuditLog")
    def test_on_feedback_positive(self, mock_audit):
        like_data = MagicMock()
        like_data.liked = True
        like_data.index = (0, 1)

        FeedbackCollector.on_feedback(like_data)

        mock_audit.log_event.assert_called_once_with(
            "user_feedback",
            rating="positive",
            message_index=(0, 1),
        )

    @patch("crisprairs.rpw.feedback.AuditLog")
    def test_on_feedback_negative(self, mock_audit):
        like_data = MagicMock()
        like_data.liked = False
        like_data.index = (1, 0)

        FeedbackCollector.on_feedback(like_data)

        mock_audit.log_event.assert_called_once_with(
            "user_feedback",
            rating="negative",
            message_index=(1, 0),
        )


class TestAggregateReport:
    def test_empty_report(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        report = FeedbackCollector.aggregate_report(session_ids=[])
        assert "Sessions: 0" in report

    def test_report_with_data(self, tmp_path, monkeypatch):
        import crisprairs.rpw.audit as amod
        monkeypatch.setattr(amod, "AUDIT_DIR", tmp_path)

        # Write mock audit data
        events = [
            {"event": "llm_call", "latency_ms": 500},
            {"event": "user_feedback", "rating": "positive"},
            {"event": "user_feedback", "rating": "positive"},
            {"event": "user_feedback", "rating": "negative"},
        ]
        audit_file = tmp_path / "s1.jsonl"
        with open(audit_file, "w") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

        report = FeedbackCollector.aggregate_report(session_ids=["s1"])
        assert "Sessions: 1" in report
        assert "Interactions: 1" in report
        assert "Positive: 67%" in report
