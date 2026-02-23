"""Integration tests: end-to-end pipeline flows with mocked LLM/API calls."""

from unittest.mock import patch

from crisprairs.engine.context import SessionContext
from crisprairs.engine.runner import PipelineRunner
from crisprairs.engine.workflow import Router, StepResult


def _build_router() -> Router:
    """Build the full workflow router (same as app.py but without gradio import)."""
    from crisprairs.workflows.activation_repression import (
        ActRepEntry,
        ActRepGuideDesign,
        ActRepSystemSelect,
        ActRepTarget,
    )
    from crisprairs.workflows.automation import AutomationStep
    from crisprairs.workflows.base_editing import (
        BaseEditingEntry,
        BaseEditingGuideDesign,
        BaseEditingSystemSelect,
        BaseEditingTarget,
    )
    from crisprairs.workflows.delivery import DeliveryEntry, DeliverySelect
    from crisprairs.workflows.evidence import EvidenceRiskStep, EvidenceScanStep
    from crisprairs.workflows.knockout import (
        KnockoutGuideDesign,
        KnockoutGuideSelection,
        KnockoutTargetInput,
    )
    from crisprairs.workflows.off_target import (
        OffTargetEntry,
        OffTargetInput,
        OffTargetReport,
        OffTargetScoring,
    )
    from crisprairs.workflows.prime_editing import (
        PrimeEditingEntry,
        PrimeEditingGuideDesign,
        PrimeEditingSystemSelect,
        PrimeEditingTarget,
    )
    from crisprairs.workflows.troubleshoot import (
        TroubleshootAdvise,
        TroubleshootDiagnose,
        TroubleshootEntry,
    )
    from crisprairs.workflows.validation import (
        BlastCheckStep,
        PrimerDesignStep,
        ValidationEntry,
    )

    router = Router()
    router.register("knockout", [
        KnockoutTargetInput(), EvidenceScanStep(), KnockoutGuideDesign(), KnockoutGuideSelection(),
        DeliveryEntry(), DeliverySelect(),
        ValidationEntry(), PrimerDesignStep(), BlastCheckStep(),
        EvidenceRiskStep(),
        AutomationStep(),
    ])
    router.register("base_editing", [
        BaseEditingEntry(), BaseEditingSystemSelect(), BaseEditingTarget(),
        EvidenceScanStep(),
        BaseEditingGuideDesign(),
        DeliveryEntry(), DeliverySelect(),
        ValidationEntry(), PrimerDesignStep(), BlastCheckStep(), EvidenceRiskStep(),
    ])
    router.register("prime_editing", [
        PrimeEditingEntry(), PrimeEditingSystemSelect(), PrimeEditingTarget(),
        EvidenceScanStep(),
        PrimeEditingGuideDesign(),
        DeliveryEntry(), DeliverySelect(),
        ValidationEntry(), PrimerDesignStep(), BlastCheckStep(), EvidenceRiskStep(),
    ])
    router.register("activation", [
        ActRepEntry(), ActRepSystemSelect(), ActRepTarget(), EvidenceScanStep(),
        ActRepGuideDesign(),
        DeliveryEntry(), DeliverySelect(), EvidenceRiskStep(),
    ])
    router.register("repression", [
        ActRepEntry(), ActRepSystemSelect(), ActRepTarget(), EvidenceScanStep(),
        ActRepGuideDesign(),
        DeliveryEntry(), DeliverySelect(), EvidenceRiskStep(),
    ])
    router.register("off_target", [
        OffTargetEntry(), OffTargetInput(), EvidenceScanStep(), OffTargetScoring(),
        OffTargetReport(), EvidenceRiskStep(),
    ])
    router.register("troubleshoot", [
        TroubleshootEntry(), EvidenceScanStep(), TroubleshootDiagnose(), TroubleshootAdvise(),
        EvidenceRiskStep(),
    ])
    return router


class TestKnockoutPipeline:
    """Test the full knockout workflow end-to-end."""

    @patch("crisprairs.apis.blast.check_primer_specificity")
    @patch("crisprairs.apis.primer3_api.design_primers")
    @patch("crisprairs.apis.ensembl.get_sequence")
    @patch("crisprairs.apis.ensembl.lookup_gene_id")
    @patch("crisprairs.apis.crispor.design_guides")
    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_full_knockout_flow(
        self, mock_chat, mock_crispor, mock_lookup, mock_seq,
        mock_primers, mock_blast,
    ):
        # Set up mocks
        mock_chat.side_effect = [
            # KnockoutTargetInput
            {"Target gene": "BRCA1", "Species": "human", "Preferred exon": "exon 2"},
            # KnockoutGuideSelection
            {"Selection": "top3"},
            # DeliverySelect
            {
                "delivery_method": "lipofection",
                "format": "plasmid",
                "reasoning": "Easy to transfect",
                "specific_product": "Lipofectamine 3000",
                "alternatives": "",
            },
            # BlastCheckStep
            {"Choice": "no"},
        ]
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
        ]
        mock_primers.return_value = [
            {
                "forward_seq": "AAAA",
                "reverse_seq": "TTTT",
                "product_size": 400,
                "forward_tm": 60.0,
                "reverse_tm": 59.0,
            },
        ]

        with patch(
            "crisprairs.workflows.evidence.run_literature_scan",
            return_value={"query": "q", "hits": [], "notes": []},
        ):
            with patch(
                "crisprairs.workflows.evidence.run_evidence_risk_review",
                return_value={"papers_reviewed": 0, "papers_flagged": 0, "risks": [], "hits": []},
            ):
                router = _build_router()
                runner = PipelineRunner(router)
                ctx = SessionContext()

                # Start knockout
                out = runner.start("knockout", ctx)
                # First step needs input (KnockoutTargetInput)
                assert out.result == StepResult.WAIT_FOR_INPUT

                # Submit target info
                out = runner.submit_input(ctx, "BRCA1 in human cells")
                assert ctx.target_gene == "BRCA1"

                # Auto-advance through guide design (KnockoutGuideDesign)
                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                # Guide selection needs input
                assert out.result == StepResult.WAIT_FOR_INPUT
                out = runner.submit_input(ctx, "use top 3")

                # Auto-advance through remaining steps, submitting input as needed
                max_iterations = 30
                for _ in range(max_iterations):
                    if runner.is_done or out.result == StepResult.DONE:
                        break
                    if out.result == StepResult.CONTINUE:
                        out = runner.advance(ctx)
                    elif out.result == StepResult.WAIT_FOR_INPUT:
                        # Submit generic input; mocks handle the responses
                        out = runner.submit_input(ctx, "yes proceed")

                # Verify final state
                assert ctx.target_gene == "BRCA1"
                assert ctx.species == "human"
                assert ctx.delivery.method == "lipofection"
                assert len(ctx.guides) >= 1


class TestBaseEditingPipeline:
    """Test base editing workflow end-to-end."""

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_base_editing_to_guide_design(self, mock_chat):
        mock_chat.side_effect = [
            # BaseEditingSystemSelect
            {"Answer": "CBE"},
            # BaseEditingTarget
            {"Target gene": "PCSK9", "Species": "human", "Base change": "C>T at position 6"},
            # BaseEditingGuideDesign
            {"Choice": "yes"},
            # DeliverySelect
            {
                "delivery_method": "electroporation",
                "format": "RNP",
                "reasoning": "Better for base editing",
                "specific_product": "Lonza 4D",
                "alternatives": "",
            },
            # BlastCheckStep
            {"Choice": "no"},
        ]

        with patch(
            "crisprairs.workflows.evidence.run_literature_scan",
            return_value={"query": "q", "hits": [], "notes": []},
        ):
            with patch(
                "crisprairs.workflows.evidence.run_evidence_risk_review",
                return_value={"papers_reviewed": 0, "papers_flagged": 0, "risks": [], "hits": []},
            ):
                router = _build_router()
                runner = PipelineRunner(router)
                ctx = SessionContext()

                out = runner.start("base_editing", ctx)
                # BaseEditingEntry auto-continues
                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                # BaseEditingSystemSelect needs input
                assert out.result == StepResult.WAIT_FOR_INPUT
                out = runner.submit_input(ctx, "CBE please")
                assert ctx.base_editor == "CBE"

                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                # BaseEditingTarget needs input
                out = runner.submit_input(ctx, "PCSK9 C to T")
                assert ctx.target_gene == "PCSK9"

                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                # BaseEditingGuideDesign needs input
                out = runner.submit_input(ctx, "yes")

                # Continue through delivery + validation
                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                if out.result == StepResult.WAIT_FOR_INPUT:
                    out = runner.submit_input(ctx, "electroporation")
                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)
                if out.result == StepResult.WAIT_FOR_INPUT:
                    out = runner.submit_input(ctx, "no")

                assert ctx.base_editor == "CBE"
                assert ctx.target_gene == "PCSK9"


class TestTroubleshootPipeline:
    """Test troubleshooting workflow end-to-end."""

    @patch("crisprairs.llm.provider.ChatProvider.chat")
    def test_troubleshoot_flow(self, mock_chat):
        mock_chat.side_effect = [
            # TroubleshootEntry
            {"Category": "low_efficiency", "Summary": "Low editing efficiency"},
            # TroubleshootDiagnose
            {
                "Diagnosis": [{"probability": "high", "cause": "Poor guide"}],
                "Key_Question": "What guide did you use?",
            },
            # TroubleshootAdvise
            {
                "Actions": [
                    {
                        "priority": 1,
                        "action": "Try new guides",
                        "expected_impact": "5x improvement",
                    },
                ],
                "Summary": "Focus on guide quality",
            },
        ]

        with patch(
            "crisprairs.workflows.evidence.run_literature_scan",
            return_value={"query": "q", "hits": [], "notes": []},
        ):
            with patch(
                "crisprairs.workflows.evidence.run_evidence_risk_review",
                return_value={"papers_reviewed": 0, "papers_flagged": 0, "risks": [], "hits": []},
            ):
                router = _build_router()
                runner = PipelineRunner(router)
                ctx = SessionContext()

                out = runner.start("troubleshoot", ctx)
                assert out.result == StepResult.WAIT_FOR_INPUT

                out = runner.submit_input(ctx, "My editing efficiency is low")
                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                out = runner.submit_input(ctx, "I used lipofection with HEK293T")
                while out.result == StepResult.CONTINUE:
                    out = runner.advance(ctx)

                # TroubleshootAdvise is auto (no needs_input), should run and finish
                assert runner.is_done or out.result == StepResult.DONE
                assert ctx.troubleshoot_issue == "low_efficiency"
                assert len(ctx.troubleshoot_recommendations) >= 1


class TestProtocolExport:
    """Test protocol generation from a populated context."""

    def test_protocol_from_context(self):
        from crisprairs.engine.context import DeliveryInfo, GuideRNA
        from crisprairs.rpw.protocols import ProtocolGenerator

        ctx = SessionContext(
            target_gene="BRCA1",
            species="human",
            cas_system="SpCas9",
            modality="knockout",
            guides=[
                GuideRNA(sequence="ATCGATCGATCGATCGATCG", score=85.0, source="crispor"),
            ],
            delivery=DeliveryInfo(
                method="lipofection",
                format="plasmid",
                product="Lipofectamine 3000",
            ),
        )

        md = ProtocolGenerator.generate(ctx, session_id="test-123")

        assert "BRCA1" in md
        assert "SpCas9" in md
        assert "Knockout" in md
        assert "ATCGATCGATCGATCGATCG" in md
        assert "Lipofectamine" in md
        assert "test-123" in md
        assert "T7E1" in md or "T7 Endonuclease" in md
