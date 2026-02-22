"""Tests for the delivery workflow."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.delivery import DeliveryEntry, DeliverySelect


class TestDeliveryEntry:
    def test_returns_continue(self):
        ctx = SessionContext()
        step = DeliveryEntry()
        out = step.execute(ctx)
        assert out.result == StepResult.CONTINUE
        assert out.message

    def test_shows_experiment_context(self):
        ctx = SessionContext(
            modality="knockout",
            cas_system="SpCas9",
            target_gene="BRCA1",
            species="human",
        )
        step = DeliveryEntry()
        out = step.execute(ctx)

        assert "knockout" in out.message
        assert "SpCas9" in out.message
        assert "BRCA1" in out.message
        assert "human" in out.message

    def test_sacas9_note(self):
        ctx = SessionContext(cas_system="SaCas9")
        step = DeliveryEntry()
        out = step.execute(ctx)

        assert "AAV" in out.message

    def test_cas12a_note(self):
        ctx = SessionContext(cas_system="enCas12a")
        step = DeliveryEntry()
        out = step.execute(ctx)

        assert "Cas12a" in out.message


class TestDeliverySelect:
    def test_needs_input(self):
        step = DeliverySelect()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_lipofection(self, mock_chat):
        mock_chat.return_value = {
            "delivery_method": "lipofection",
            "format": "plasmid",
            "reasoning": "HEK293T cells are easy to transfect",
            "specific_product": "Lipofectamine 3000",
            "alternatives": "electroporation",
        }
        ctx = SessionContext()
        step = DeliverySelect()
        out = step.execute(ctx, user_input="HEK293T cells, standard lab setup")

        assert out.result == StepResult.DONE
        assert ctx.delivery.method == "lipofection"
        assert ctx.delivery.format == "plasmid"
        assert ctx.delivery.product == "Lipofectamine 3000"
        assert "lipofection" in out.message
        assert "Alternative" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_no_alternatives(self, mock_chat):
        mock_chat.return_value = {
            "delivery_method": "electroporation",
            "format": "RNP",
            "reasoning": "Primary T cells require electroporation",
            "specific_product": "Lonza 4D Nucleofector",
            "alternatives": "",
        }
        ctx = SessionContext()
        step = DeliverySelect()
        out = step.execute(ctx, user_input="Primary T cells")

        assert ctx.delivery.method == "electroporation"
        assert "Alternative" not in out.message
