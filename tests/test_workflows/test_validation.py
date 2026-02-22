"""Tests for the validation workflow."""

from unittest.mock import patch

from crisprairs.engine.context import PrimerPair, SessionContext
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.validation import (
    BlastCheckStep,
    PrimerDesignStep,
    ValidationEntry,
)


class TestValidationEntry:
    def test_returns_continue(self):
        ctx = SessionContext()
        step = ValidationEntry()
        out = step.execute(ctx)
        assert out.result == StepResult.CONTINUE
        assert out.message


class TestPrimerDesignStep:
    def test_no_target_gene(self):
        ctx = SessionContext()
        step = PrimerDesignStep()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert "Primer3" in out.message

    @patch("crisprairs.apis.primer3_api.design_primers")
    @patch("crisprairs.apis.ensembl.get_sequence")
    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    def test_designs_primers(self, mock_lookup, mock_seq, mock_primers):
        mock_lookup.return_value = "ENSG00000012048"
        mock_seq.return_value = {"full_sequence": "A" * 1000}
        mock_primers.return_value = [
            {
                "forward_seq": "ATCGATCGATCG",
                "reverse_seq": "GCTAGCTAGCTA",
                "product_size": 450,
                "forward_tm": 60.5,
                "reverse_tm": 59.8,
            },
        ]
        ctx = SessionContext(target_gene="BRCA1", species="human")
        step = PrimerDesignStep()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert len(ctx.primers) == 1
        assert ctx.primers[0].forward == "ATCGATCGATCG"
        assert "ATCGATCGATCG" in out.message

    @patch("crisprairs.apis.primer3_api.design_primers")
    @patch("crisprairs.apis.ensembl.get_sequence")
    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    def test_no_primer_results(self, mock_lookup, mock_seq, mock_primers):
        mock_lookup.return_value = "ENSG00000012048"
        mock_seq.return_value = {"full_sequence": "A" * 1000}
        mock_primers.return_value = []

        ctx = SessionContext(target_gene="BRCA1", species="human")
        step = PrimerDesignStep()
        out = step.execute(ctx)

        assert "no results" in out.message.lower()

    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    def test_handles_lookup_failure(self, mock_lookup):
        mock_lookup.return_value = None
        ctx = SessionContext(target_gene="BRCA1", species="human")
        step = PrimerDesignStep()
        out = step.execute(ctx)

        assert "Primer3" in out.message  # fallback message


class TestBlastCheckStep:
    def test_needs_input(self):
        step = BlastCheckStep()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_skip_blast(self, mock_chat):
        mock_chat.return_value = {"Choice": "no"}
        ctx = SessionContext()
        step = BlastCheckStep()
        out = step.execute(ctx, user_input="no")

        assert out.result == StepResult.DONE
        assert "Skipping" in out.message

    @patch("crisprairs.apis.blast.check_primer_specificity")
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_specific_primers(self, mock_chat, mock_blast):
        mock_chat.return_value = {"Choice": "yes"}
        mock_blast.return_value = {
            "specific": True,
            "forward_hits": 1,
            "reverse_hits": 1,
        }
        ctx = SessionContext(
            species="human",
            primers=[PrimerPair(forward="ATCG", reverse="GCTA")],
        )
        step = BlastCheckStep()
        out = step.execute(ctx, user_input="yes")

        assert out.result == StepResult.DONE
        assert "specific" in out.message.lower()
        assert ctx.primers[0].blast_status == "specific"

    @patch("crisprairs.apis.blast.check_primer_specificity")
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_nonspecific_primers(self, mock_chat, mock_blast):
        mock_chat.return_value = {"Choice": "yes"}
        mock_blast.return_value = {
            "specific": False,
            "forward_hits": 5,
            "reverse_hits": 3,
        }
        ctx = SessionContext(
            species="human",
            primers=[PrimerPair(forward="ATCG", reverse="GCTA")],
        )
        step = BlastCheckStep()
        out = step.execute(ctx, user_input="yes check them")

        assert ctx.primers[0].blast_status == "non-specific"
        assert "redesigning" in out.message.lower()
