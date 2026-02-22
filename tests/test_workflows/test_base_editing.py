"""Tests for the base editing workflow."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.base_editing import (
    BaseEditingEntry,
    BaseEditingGuideDesign,
    BaseEditingSystemSelect,
    BaseEditingTarget,
)


class TestBaseEditingEntry:
    def test_returns_continue(self):
        ctx = SessionContext()
        step = BaseEditingEntry()
        out = step.execute(ctx)
        assert out.result == StepResult.CONTINUE
        assert out.message  # non-empty


class TestBaseEditingSystemSelect:
    def test_needs_input(self):
        step = BaseEditingSystemSelect()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_cbe(self, mock_chat):
        mock_chat.return_value = {"Answer": "CBE"}
        ctx = SessionContext()
        step = BaseEditingSystemSelect()
        out = step.execute(ctx, user_input="I want to do C to T editing")

        assert out.result == StepResult.CONTINUE
        assert ctx.base_editor == "CBE"
        assert "CBE" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_abe(self, mock_chat):
        mock_chat.return_value = {"Answer": "ABE"}
        ctx = SessionContext()
        step = BaseEditingSystemSelect()
        step.execute(ctx, user_input="A to G change")

        assert ctx.base_editor == "ABE"


class TestBaseEditingTarget:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_parses_target(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "PCSK9",
            "Species": "human",
            "Base change": "C>T at position 6",
        }
        ctx = SessionContext(base_editor="CBE")
        step = BaseEditingTarget()
        out = step.execute(ctx, user_input="PCSK9 in human, C to T")

        assert ctx.target_gene == "PCSK9"
        assert ctx.species == "human"
        assert ctx.target_base_change == "C>T at position 6"
        assert "4-8" in out.message  # CBE editing window

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_abe_editing_window(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "HBB",
            "Species": "human",
            "Base change": "A>G",
        }
        ctx = SessionContext(base_editor="ABE")
        step = BaseEditingTarget()
        out = step.execute(ctx, user_input="HBB A to G")

        assert "4-7" in out.message  # ABE editing window

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_warns_cbe_with_ag_change(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "HBB",
            "Species": "human",
            "Base change": "A>G at position 5",
        }
        ctx = SessionContext(base_editor="CBE")
        step = BaseEditingTarget()
        out = step.execute(ctx, user_input="HBB A>G")

        assert "Consider switching to ABE" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_warns_abe_with_ct_change(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "HBB",
            "Species": "human",
            "Base change": "C>T at position 5",
        }
        ctx = SessionContext(base_editor="ABE")
        step = BaseEditingTarget()
        out = step.execute(ctx, user_input="HBB C>T")

        assert "Consider switching to CBE" in out.message


class TestBaseEditingGuideDesign:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_yes_returns_resources(self, mock_chat):
        mock_chat.return_value = {"Choice": "yes"}
        ctx = SessionContext(base_editor="CBE", target_gene="PCSK9")
        step = BaseEditingGuideDesign()
        out = step.execute(ctx, user_input="yes please design guides")

        assert out.result == StepResult.DONE
        assert "BE-Designer" in out.message
        assert "4-8" in out.message  # CBE window

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_no_returns_resources(self, mock_chat):
        mock_chat.return_value = {"Choice": "no"}
        ctx = SessionContext(base_editor="ABE", target_gene="HBB")
        step = BaseEditingGuideDesign()
        out = step.execute(ctx, user_input="no thanks")

        assert out.result == StepResult.DONE
        assert "BE-Designer" in out.message
