"""Tests for the protocol generator module."""

from crisprairs.engine.context import DeliveryInfo, GuideRNA, SessionContext
from crisprairs.rpw.protocols import REAGENT_CATALOG, ProtocolGenerator


class TestProtocolGenerator:
    def test_basic_protocol(self):
        ctx = SessionContext(
            target_gene="BRCA1",
            species="human",
            cas_system="SpCas9",
            modality="knockout",
        )
        md = ProtocolGenerator.generate(ctx)

        assert "BRCA1" in md
        assert "human" in md
        assert "SpCas9" in md
        assert "Knockout" in md
        assert "## Materials" in md
        assert "## Experimental Steps" in md
        assert "## Controls" in md
        assert "## Expected Results" in md

    def test_session_id_included(self):
        ctx = SessionContext(target_gene="TP53")
        md = ProtocolGenerator.generate(ctx, session_id="abc123")
        assert "abc123" in md

    def test_knockout_validation(self):
        ctx = SessionContext(modality="knockout", target_gene="BRCA1")
        md = ProtocolGenerator.generate(ctx)
        assert "T7E1" in md or "T7 Endonuclease" in md

    def test_base_editing_validation(self):
        ctx = SessionContext(modality="base_editing", target_gene="PCSK9")
        md = ProtocolGenerator.generate(ctx)
        assert "Base Editing" in md
        assert "base conversion" in md.lower() or "EditR" in md

    def test_prime_editing_validation(self):
        ctx = SessionContext(modality="prime_editing", target_gene="HBB")
        md = ProtocolGenerator.generate(ctx)
        assert "Prime Editing" in md
        assert "CRISPResso2" in md

    def test_crispra_validation(self):
        ctx = SessionContext(modality="activation", target_gene="MYC")
        md = ProtocolGenerator.generate(ctx)
        assert "CRISPRa/CRISPRi" in md
        assert "RT-qPCR" in md

    def test_lipofection_delivery(self):
        ctx = SessionContext(
            cas_system="SpCas9",
            delivery=DeliveryInfo(method="lipofection", format="plasmid"),
        )
        md = ProtocolGenerator.generate(ctx)
        assert "Lipofectamine" in md or "lipofection" in md.lower()

    def test_electroporation_delivery(self):
        ctx = SessionContext(
            delivery=DeliveryInfo(
                method="electroporation",
                format="RNP",
                product="Lonza 4D-Nucleofector",
            ),
        )
        md = ProtocolGenerator.generate(ctx)
        assert "Lonza" in md
        assert "RNP" in md

    def test_sgrna_section_with_guides(self):
        ctx = SessionContext(
            guides=[
                GuideRNA(sequence="ATCGATCGATCGATCGATCG", score=85.0, source="crispor"),
                GuideRNA(sequence="GCTAGCTAGCTAGCTAGCTA", score=70.0, source="crispor"),
            ],
        )
        md = ProtocolGenerator.generate(ctx)
        assert "ATCGATCGATCGATCGATCG" in md
        assert "crispor" in md

    def test_sgrna_section_no_guides(self):
        ctx = SessionContext()
        md = ProtocolGenerator.generate(ctx)
        assert "No sgRNA data" in md

    def test_reagent_catalog_coverage(self):
        assert "SpCas9" in REAGENT_CATALOG
        assert "common" in REAGENT_CATALOG
        assert "plasmid" in REAGENT_CATALOG["SpCas9"]

    def test_off_target_protocol_not_mislabeled_as_knockout(self):
        ctx = SessionContext(modality="off_target")
        md = ProtocolGenerator.generate(ctx)
        assert "**Modality:** Off-Target Analysis" in md
        assert "## Analysis Summary" in md
        assert "## Controls" not in md

    def test_troubleshooting_protocol_not_mislabeled_as_knockout(self):
        ctx = SessionContext(modality="troubleshoot")
        md = ProtocolGenerator.generate(ctx)
        assert "**Modality:** Troubleshooting" in md
        assert "## Troubleshooting Summary" in md
        assert "## Expected Results" not in md


class TestResolveModality:
    def test_knockout_default(self):
        ctx = SessionContext()
        assert ProtocolGenerator._resolve_modality(ctx) == "Knockout"

    def test_base_editing(self):
        ctx = SessionContext(modality="base_editing")
        assert ProtocolGenerator._resolve_modality(ctx) == "Base Editing"

    def test_prime_editing(self):
        ctx = SessionContext(modality="prime_editing")
        assert ProtocolGenerator._resolve_modality(ctx) == "Prime Editing"

    def test_activation(self):
        ctx = SessionContext(modality="activation")
        assert ProtocolGenerator._resolve_modality(ctx) == "CRISPRa/CRISPRi"

    def test_off_target(self):
        ctx = SessionContext(modality="off_target")
        assert ProtocolGenerator._resolve_modality(ctx) == "Off-Target Analysis"

    def test_troubleshoot(self):
        ctx = SessionContext(modality="troubleshoot")
        assert ProtocolGenerator._resolve_modality(ctx) == "Troubleshooting"
