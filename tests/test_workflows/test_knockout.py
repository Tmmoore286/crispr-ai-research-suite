"""Tests for the knockout workflow."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext, GuideRNA
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.knockout import (
    KnockoutTargetInput,
    KnockoutGuideDesign,
    KnockoutGuideSelection,
)


class TestKnockoutTargetInput:
    def test_needs_input(self):
        step = KnockoutTargetInput()
        assert step.needs_input is True
        assert step.prompt_message  # non-empty prompt

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_parses_target_and_species(self, mock_chat):
        mock_chat.return_value = {
            "Target gene": "BRCA1",
            "Species": "human",
            "Preferred exon": "exon 10",
        }
        ctx = SessionContext()
        step = KnockoutTargetInput()
        out = step.execute(ctx, user_input="I want to knock out BRCA1 in human cells")

        assert out.result == StepResult.CONTINUE
        assert ctx.target_gene == "BRCA1"
        assert ctx.species == "human"
        assert ctx.extra["preferred_exon"] == "exon 10"
        assert "BRCA1" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_default_cas_system(self, mock_chat):
        mock_chat.return_value = {"Target gene": "TP53", "Species": "mouse"}
        ctx = SessionContext()
        step = KnockoutTargetInput()
        step.execute(ctx, user_input="TP53 in mouse")

        assert ctx.cas_system == "SpCas9"

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_preserves_existing_cas_system(self, mock_chat):
        mock_chat.return_value = {"Target gene": "TP53", "Species": "mouse"}
        ctx = SessionContext(cas_system="SaCas9")
        step = KnockoutTargetInput()
        step.execute(ctx, user_input="TP53 in mouse")

        assert ctx.cas_system == "SaCas9"


class TestKnockoutGuideDesign:
    def test_no_target_gene(self):
        ctx = SessionContext()
        step = KnockoutGuideDesign()
        out = step.execute(ctx)

        assert out.result == StepResult.WAIT_FOR_INPUT
        assert "No target gene" in out.message

    @patch("crisprairs.apis.crispor.design_guides")
    @patch("crisprairs.apis.ensembl.get_sequence")
    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    def test_designs_guides_via_api(self, mock_lookup, mock_seq, mock_crispor):
        mock_lookup.return_value = "ENSG00000012048"
        mock_seq.return_value = {"full_sequence": "A" * 500}
        mock_crispor.return_value = [
            {
                "guide_sequence": "ATCGATCGATCGATCGATCG",
                "pam": "NGG",
                "mit_specificity_score": 85.0,
                "off_target_count": 3,
                "doench2016_score": 0.7,
                "position": "100",
            },
            {
                "guide_sequence": "GCTAGCTAGCTAGCTAGCTA",
                "pam": "NGG",
                "mit_specificity_score": 70.0,
                "off_target_count": 8,
                "doench2016_score": 0.5,
                "position": "200",
            },
        ]

        ctx = SessionContext(target_gene="BRCA1", species="human")
        step = KnockoutGuideDesign()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert len(ctx.guides) == 2
        assert ctx.guides[0].sequence == "ATCGATCGATCGATCGATCG"
        assert ctx.guides[0].score == 85.0
        assert ctx.guides[0].source == "crispor"
        assert "ATCGATCGATCGATCGATCG" in out.message

    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    def test_handles_api_failure(self, mock_lookup):
        mock_lookup.return_value = None

        ctx = SessionContext(target_gene="BRCA1", species="human")
        step = KnockoutGuideDesign()
        out = step.execute(ctx)

        assert out.result == StepResult.CONTINUE
        assert len(ctx.guides) == 0
        assert "Could not retrieve" in out.message

    @patch("crisprairs.apis.ensembl.get_sequence")
    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    def test_handles_short_sequence(self, mock_lookup, mock_seq):
        mock_lookup.return_value = "ENSG00000012048"
        mock_seq.return_value = {"full_sequence": "ATCG"}

        ctx = SessionContext(target_gene="BRCA1", species="human")
        step = KnockoutGuideDesign()
        out = step.execute(ctx)

        assert len(ctx.guides) == 0
        assert "Could not retrieve" in out.message


class TestKnockoutGuideSelection:
    def test_needs_input(self):
        step = KnockoutGuideSelection()
        assert step.needs_input is True

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_selects_guides(self, mock_chat):
        mock_chat.return_value = {"Selection": "top3"}
        ctx = SessionContext(
            target_gene="BRCA1",
            guides=[
                GuideRNA(sequence="AAAA", score=90.0),
                GuideRNA(sequence="BBBB", score=80.0),
                GuideRNA(sequence="CCCC", score=70.0),
            ],
        )
        step = KnockoutGuideSelection()
        out = step.execute(ctx, user_input="use top 3")

        assert out.result == StepResult.DONE
        assert "3 guide(s)" in out.message
        assert "BRCA1" in out.message

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_no_guides_available(self, mock_chat):
        mock_chat.return_value = {"Selection": "all"}
        ctx = SessionContext(target_gene="BRCA1")
        step = KnockoutGuideSelection()
        out = step.execute(ctx, user_input="all")

        assert out.result == StepResult.DONE
        assert "No guides available" in out.message
