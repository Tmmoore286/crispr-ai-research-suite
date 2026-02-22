"""Tests for engine/context.py — SessionContext, GuideRNA, DeliveryInfo, PrimerPair."""

from crisprairs.engine.context import (
    SessionContext,
    GuideRNA,
    DeliveryInfo,
    PrimerPair,
)


class TestGuideRNA:
    def test_defaults(self):
        g = GuideRNA()
        assert g.sequence == ""
        assert g.score == 0.0
        assert g.metadata == {}

    def test_with_values(self):
        g = GuideRNA(sequence="ATCGATCG", score=95.5, source="crispor")
        assert g.sequence == "ATCGATCG"
        assert g.score == 95.5
        assert g.source == "crispor"


class TestDeliveryInfo:
    def test_defaults(self):
        d = DeliveryInfo()
        assert d.method == ""
        assert d.format == ""

    def test_with_values(self):
        d = DeliveryInfo(method="electroporation", format="RNP", product="Lonza 4D")
        assert d.method == "electroporation"
        assert d.product == "Lonza 4D"


class TestPrimerPair:
    def test_defaults(self):
        p = PrimerPair()
        assert p.forward == ""
        assert p.product_size == 0

    def test_with_values(self):
        p = PrimerPair(forward="ATCG", reverse="GCTA", product_size=500)
        assert p.product_size == 500


class TestSessionContext:
    def test_defaults(self):
        ctx = SessionContext()
        assert ctx.target_gene == ""
        assert ctx.species == ""
        assert ctx.modality == ""
        assert ctx.guides == []
        assert isinstance(ctx.delivery, DeliveryInfo)
        assert ctx.session_id  # auto-generated

    def test_custom_session_id(self):
        ctx = SessionContext(session_id="test-123")
        assert ctx.session_id == "test-123"

    def test_unique_session_ids(self):
        ctx1 = SessionContext()
        ctx2 = SessionContext()
        assert ctx1.session_id != ctx2.session_id

    def test_mutability(self):
        ctx = SessionContext()
        ctx.target_gene = "BRCA1"
        ctx.species = "human"
        ctx.modality = "knockout"
        assert ctx.target_gene == "BRCA1"
        assert ctx.species == "human"

    def test_guide_list(self):
        ctx = SessionContext()
        ctx.guides.append(GuideRNA(sequence="ATCG", score=90.0))
        assert len(ctx.guides) == 1
        assert ctx.guides[0].score == 90.0

    def test_to_dict(self):
        ctx = SessionContext(session_id="abc", target_gene="TP53", species="human")
        d = ctx.to_dict()
        assert d["session_id"] == "abc"
        assert d["target_gene"] == "TP53"
        assert isinstance(d["delivery"], dict)
        assert isinstance(d["guides"], list)

    def test_from_dict_roundtrip(self):
        original = SessionContext(
            session_id="test-rt",
            target_gene="BRCA1",
            species="mouse",
            modality="base_editing",
            cas_system="SpCas9",
        )
        original.guides.append(GuideRNA(sequence="ATCGATCG", score=85.0))
        original.delivery = DeliveryInfo(method="electroporation", format="RNP")
        original.primers.append(PrimerPair(forward="AAA", reverse="TTT", product_size=300))

        d = original.to_dict()
        restored = SessionContext.from_dict(d)

        assert restored.session_id == "test-rt"
        assert restored.target_gene == "BRCA1"
        assert restored.species == "mouse"
        assert len(restored.guides) == 1
        assert restored.guides[0].sequence == "ATCGATCG"
        assert restored.delivery.method == "electroporation"
        assert len(restored.primers) == 1
        assert restored.primers[0].product_size == 300

    def test_from_dict_ignores_unknown_keys(self):
        data = {"session_id": "x", "target_gene": "TP53", "unknown_field": "ignored"}
        ctx = SessionContext.from_dict(data)
        assert ctx.target_gene == "TP53"

    def test_extra_dict(self):
        ctx = SessionContext()
        ctx.extra["custom_key"] = "custom_value"
        assert ctx.extra["custom_key"] == "custom_value"

    def test_chat_history(self):
        ctx = SessionContext()
        ctx.chat_history.append(("user msg", "bot msg"))
        assert len(ctx.chat_history) == 1
        assert ctx.chat_history[0] == ("user msg", "bot msg")
