"""Tests for the prime editing workflow."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.prime_editing import (
    PrimeEditingEntry,
    PrimeEditingSystemSelect,
    PrimeEditingTarget,
    PrimeEditingGuideDesign,
)


class TestPrimeEditingEntry:
    def test_returns_continue(self):
        ctx = SessionContext()
        step = PrimeEditingEntry()
        out = step.execute(ctx)
        assert out.result == StepResult.CONTINUE
        assert out.message


class TestPrimeEditingSystemSelect:
    def test_needs_input(self):
        step = PrimeEditingSystemSelect()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_pe2(self, mock_chat):
        mock_chat.return_value = {"Answer": "PE2"}
        ctx = SessionContext()
        step = PrimeEditingSystemSelect()
        out = step.execute(ctx, user_input="PE2")

        assert ctx.prime_editor == "PE2"
        assert "PE2" in out.message
        assert "nicking" not in out.message.lower()

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_pe3_shows_nicking_note(self, mock_chat):
        mock_chat.return_value = {"Answer": "PE3"}
        ctx = SessionContext()
        step = PrimeEditingSystemSelect()
        out = step.execute(ctx, user_input="PE3")

        assert ctx.prime_editor == "PE3"
        assert "nicking" in out.message.lower()

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_pe3b_shows_nicking_note(self, mock_chat):
        mock_chat.return_value = {"Answer": "PE3b"}
        ctx = SessionContext()
        step = PrimeEditingSystemSelect()
        out = step.execute(ctx, user_input="PE3b")

        assert "nicking" in out.message.lower()


class TestPrimeEditingTarget:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_parses_target(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "HBB",
            "Species": "human",
            "Edit type": "point_mutation",
            "Edit description": "E6V correction (sickle cell)",
        }
        ctx = SessionContext(prime_editor="PE2")
        step = PrimeEditingTarget()
        out = step.execute(ctx, user_input="correct sickle cell mutation in HBB")

        assert ctx.target_gene == "HBB"
        assert ctx.species == "human"
        assert ctx.extra["edit_type"] == "point_mutation"
        assert "pegRNA" in out.message
        assert "PE2" in out.message


class TestPrimeEditingGuideDesign:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_yes_with_pe2(self, mock_chat):
        mock_chat.return_value = {
            "Choice": "yes",
            "PBS_length": "13",
            "RT_template_length": "15",
        }
        ctx = SessionContext(prime_editor="PE2", target_gene="HBB")
        step = PrimeEditingGuideDesign()
        out = step.execute(ctx, user_input="yes")

        assert out.result == StepResult.DONE
        assert "PrimeDesign" in out.message
        assert "13" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_yes_with_pe3_shows_nicking(self, mock_chat):
        mock_chat.return_value = {
            "Choice": "yes",
            "PBS_length": "13",
            "RT_template_length": "15",
        }
        ctx = SessionContext(prime_editor="PE3", target_gene="HBB")
        step = PrimeEditingGuideDesign()
        out = step.execute(ctx, user_input="yes")

        assert "Nicking guide" in out.message
        assert "40-90 bp" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_no_returns_resources(self, mock_chat):
        mock_chat.return_value = {"Choice": "no"}
        ctx = SessionContext(prime_editor="PE2")
        step = PrimeEditingGuideDesign()
        out = step.execute(ctx, user_input="no")

        assert out.result == StepResult.DONE
        assert "PrimeDesign" in out.message
