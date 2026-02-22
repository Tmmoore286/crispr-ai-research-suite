"""Tests for the off-target analysis workflow."""

from unittest.mock import patch

from crisprairs.engine.context import GuideRNA, SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.off_target import (
    OffTargetEntry,
    OffTargetInput,
    OffTargetReport,
    OffTargetScoring,
)


class TestOffTargetEntry:
    def test_returns_continue(self):
        ctx = SessionContext()
        step = OffTargetEntry()
        out = step.execute(ctx)
        assert out.result == StepResult.CONTINUE
        assert out.message


class TestOffTargetInput:
    def test_needs_input(self):
        step = OffTargetInput()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_parses_guides(self, mock_chat):
        mock_chat.return_value = {
            "guides": [
                {"sequence": "ATCGATCGATCGATCGATCG", "name": "Guide1"},
                {"sequence": "GCTAGCTAGCTAGCTAGCTA", "name": "Guide2"},
            ],
            "species": "human",
            "cas_system": "SpCas9",
        }
        ctx = SessionContext()
        step = OffTargetInput()
        out = step.execute(ctx, user_input="ATCGATCGATCGATCGATCG and GCTAGCTAGCTAGCTAGCTA")

        assert out.result == StepResult.CONTINUE
        assert len(ctx.guides) == 2
        assert ctx.guides[0].sequence == "ATCGATCGATCGATCGATCG"
        assert ctx.species == "human"
        assert "2 guide(s)" in out.message


class TestOffTargetScoring:
    def test_no_guides(self):
        ctx = SessionContext()
        step = OffTargetScoring()
        out = step.execute(ctx)

        assert out.result == StepResult.WAIT_FOR_INPUT
        assert "No guides" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    @patch("crisprairs.apis.crispor.score_existing_guides")
    def test_scores_and_assesses(self, mock_score, mock_chat):
        mock_score.return_value = [
            {
                "query_sequence": "ATCGATCGATCGATCGATCG",
                "guides": [
                    {"mit_specificity_score": 90.0, "off_target_count": 2},
                ],
            },
        ]
        mock_chat.return_value = {
            "assessments": [
                {
                    "guide_name": "Guide1",
                    "sequence": "ATCGATCGATCGATCGATCG",
                    "risk_level": "low",
                    "recommendation": "Safe to use",
                },
            ],
            "overall_recommendation": "Proceed with Guide1",
        }
        ctx = SessionContext(
            species="human",
            cas_system="SpCas9",
            guides=[GuideRNA(sequence="ATCGATCGATCGATCGATCG")],
        )
        step = OffTargetScoring()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert ctx.guides[0].score == 90.0
        assert len(ctx.off_target_results) == 1
        assert "LOW" in out.message
        assert "Proceed" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    @patch("crisprairs.apis.crispor.score_existing_guides")
    def test_scoring_mapping_handles_empty_guide_entries(self, mock_score, mock_chat):
        mock_score.return_value = [
            {
                "query_sequence": "GCTAGCTAGCTAGCTAGCTA",
                "guides": [{"mit_specificity_score": 82.0, "off_target_count": 4}],
            }
        ]
        mock_chat.return_value = {"assessments": [], "overall_recommendation": ""}

        ctx = SessionContext(
            species="human",
            cas_system="SpCas9",
            guides=[
                GuideRNA(sequence=""),
                GuideRNA(sequence="GCTAGCTAGCTAGCTAGCTA"),
            ],
        )
        step = OffTargetScoring()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert ctx.guides[0].score == 0.0
        assert ctx.guides[1].score == 82.0
        assert ctx.guides[1].off_target_score == 4

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    @patch("crisprairs.apis.crispor.score_existing_guides")
    def test_scores_assign_to_correct_guide_by_sequence(self, mock_score, mock_chat):
        mock_score.return_value = [
            {
                "query_sequence": "GCTAGCTAGCTAGCTAGCTA",
                "guides": [{"mit_specificity_score": 65.0, "off_target_count": 11}],
            },
            {
                "query_sequence": "ATCGATCGATCGATCGATCG",
                "guides": [{"mit_specificity_score": 91.0, "off_target_count": 1}],
            },
        ]
        mock_chat.return_value = {"assessments": [], "overall_recommendation": ""}

        ctx = SessionContext(
            species="human",
            cas_system="SpCas9",
            guides=[
                GuideRNA(sequence="ATCGATCGATCGATCGATCG"),
                GuideRNA(sequence=""),
                GuideRNA(sequence="GCTAGCTAGCTAGCTAGCTA"),
            ],
        )
        step = OffTargetScoring()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert ctx.guides[0].score == 91.0
        assert ctx.guides[0].off_target_score == 1
        assert ctx.guides[1].score == 0.0
        assert ctx.guides[2].score == 65.0
        assert ctx.guides[2].off_target_score == 11


class TestOffTargetReport:
    def test_needs_input(self):
        step = OffTargetReport()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_yes_shows_crispritz(self, mock_chat):
        mock_chat.return_value = {"Choice": "yes"}
        ctx = SessionContext()
        step = OffTargetReport()
        out = step.execute(ctx, user_input="yes")

        assert out.result == StepResult.DONE
        assert "CRISPRitz" in out.message
        assert "github.com/pinellolab/CRISPRitz" in out.message
        assert "pip install crispritz" not in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_no_completes(self, mock_chat):
        mock_chat.return_value = {"Choice": "no"}
        ctx = SessionContext()
        step = OffTargetReport()
        out = step.execute(ctx, user_input="no")

        assert out.result == StepResult.DONE
        assert "complete" in out.message.lower()
