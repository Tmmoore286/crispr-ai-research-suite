"""Tests for the activation/repression workflow."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.activation_repression import (
    ActRepEntry,
    ActRepGuideDesign,
    ActRepSystemSelect,
    ActRepTarget,
)


class TestActRepEntry:
    def test_returns_continue(self):
        ctx = SessionContext()
        step = ActRepEntry()
        out = step.execute(ctx)
        assert out.result == StepResult.CONTINUE
        assert out.message


class TestActRepSystemSelect:
    def test_needs_input(self):
        step = ActRepSystemSelect()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_activation(self, mock_chat):
        mock_chat.return_value = {"Answer": "dCas9-VP64", "Mode": "activation"}
        ctx = SessionContext()
        step = ActRepSystemSelect()
        out = step.execute(ctx, user_input="I want to activate a gene")

        assert ctx.effector_system == "dCas9-VP64"
        assert ctx.modality == "activation"
        assert "dCas9-VP64" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_repression(self, mock_chat):
        mock_chat.return_value = {"Answer": "dCas9-KRAB", "Mode": "repression"}
        ctx = SessionContext()
        step = ActRepSystemSelect()
        step.execute(ctx, user_input="I want to silence a gene")

        assert ctx.effector_system == "dCas9-KRAB"
        assert ctx.modality == "repression"


class TestActRepTarget:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_parses_target(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "MYC",
            "Species": "human",
            "TSS targeting note": "Target within 200bp upstream of TSS",
        }
        ctx = SessionContext(effector_system="dCas9-VP64")
        step = ActRepTarget()
        out = step.execute(ctx, user_input="Activate MYC in human cells")

        assert ctx.target_gene == "MYC"
        assert ctx.species == "human"
        assert "TSS" in out.message
        assert "dCas9-VP64" in out.message


class TestActRepGuideDesign:
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_yes_returns_recommendations(self, mock_chat):
        mock_chat.return_value = {"Choice": "yes"}
        ctx = SessionContext(effector_system="dCas9-VP64", target_gene="MYC")
        step = ActRepGuideDesign()
        out = step.execute(ctx, user_input="yes")

        assert out.result == StepResult.DONE
        assert "CRISPick" in out.message
        assert "MYC" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_no_skips_design(self, mock_chat):
        mock_chat.return_value = {"Choice": "no"}
        ctx = SessionContext(effector_system="dCas9-KRAB")
        step = ActRepGuideDesign()
        out = step.execute(ctx, user_input="no")

        assert out.result == StepResult.DONE
        assert "Proceeding without" in out.message
