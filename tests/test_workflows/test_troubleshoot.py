"""Tests for the troubleshooting workflow."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.troubleshoot import (
    TroubleshootEntry,
    TroubleshootDiagnose,
    TroubleshootAdvise,
)


class TestTroubleshootEntry:
    def test_needs_input(self):
        step = TroubleshootEntry()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_categorizes_issue(self, mock_chat):
        mock_chat.return_value = {
            "Category": "low_efficiency",
            "Summary": "Low editing efficiency observed",
        }
        ctx = SessionContext()
        step = TroubleshootEntry()
        out = step.execute(ctx, user_input="My editing efficiency is very low")

        assert out.result == StepResult.CONTINUE
        assert ctx.troubleshoot_issue == "low_efficiency"
        assert ctx.extra["troubleshoot_summary"] == "Low editing efficiency observed"
        assert "low_efficiency" in out.message


class TestTroubleshootDiagnose:
    def test_needs_input(self):
        step = TroubleshootDiagnose()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_generates_diagnosis(self, mock_chat):
        mock_chat.return_value = {
            "Diagnosis": [
                {"probability": "high", "cause": "Poor guide RNA activity"},
                {"probability": "medium", "cause": "Suboptimal delivery"},
            ],
            "Key_Question": "What was the transfection efficiency?",
        }
        ctx = SessionContext(troubleshoot_issue="low_efficiency")
        ctx.extra["troubleshoot_summary"] = "Low editing efficiency"

        step = TroubleshootDiagnose()
        out = step.execute(ctx, user_input="I used lipofection with HEK293T")

        assert out.result == StepResult.CONTINUE
        assert len(ctx.extra["troubleshoot_diagnosis"]) == 2
        assert "HIGH" in out.message
        assert "transfection efficiency" in out.message


class TestTroubleshootAdvise:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_generates_plan(self, mock_chat):
        mock_chat.return_value = {
            "Actions": [
                {
                    "priority": 1,
                    "action": "Test alternative guide RNAs",
                    "expected_impact": "Potentially 5-10x improvement",
                },
                {
                    "priority": 2,
                    "action": "Optimize delivery conditions",
                    "expected_impact": "2-3x improvement",
                },
            ],
            "Summary": "Focus on guide RNA quality first",
        }
        ctx = SessionContext(troubleshoot_issue="low_efficiency")
        ctx.extra["troubleshoot_summary"] = "Low editing efficiency"
        ctx.extra["troubleshoot_diagnosis"] = [
            {"probability": "high", "cause": "Poor guide RNA"},
        ]

        step = TroubleshootAdvise()
        out = step.execute(ctx)

        assert out.result == StepResult.DONE
        assert len(ctx.troubleshoot_recommendations) == 2
        assert "alternative guide" in out.message.lower()
        assert "Focus on guide RNA" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_unknown_category_uses_other(self, mock_chat):
        mock_chat.return_value = {"Actions": [], "Summary": "No specific advice"}
        ctx = SessionContext(troubleshoot_issue="something_unknown")
        ctx.extra["troubleshoot_summary"] = "weird issue"
        ctx.extra["troubleshoot_diagnosis"] = []

        step = TroubleshootAdvise()
        out = step.execute(ctx)

        assert out.result == StepResult.DONE
