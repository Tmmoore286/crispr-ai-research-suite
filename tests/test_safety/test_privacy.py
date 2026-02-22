"""Tests for safety/privacy.py — sequence privacy detection."""

from crisprairs.safety.privacy import (
    contains_identifiable_sequences,
    WARNING_PRIVACY,
    MIN_IDENTIFIABLE_LENGTH,
)


class TestContainsIdentifiableSequences:
    def test_short_guide_rna_ok(self):
        """20-nt guide RNA should NOT be flagged."""
        assert contains_identifiable_sequences("ATCGATCGATCGATCGATCG") is False

    def test_long_sequence_flagged(self):
        """A 60-nt sequence should be flagged."""
        seq = "A" * 60
        assert contains_identifiable_sequences(seq) is True

    def test_exactly_threshold(self):
        """Exactly MIN_IDENTIFIABLE_LENGTH should be flagged."""
        seq = "ATCG" * (MIN_IDENTIFIABLE_LENGTH // 4 + 1)
        seq = seq[:MIN_IDENTIFIABLE_LENGTH]
        assert contains_identifiable_sequences(seq) is True

    def test_below_threshold(self):
        """One base below threshold should NOT be flagged."""
        seq = "A" * (MIN_IDENTIFIABLE_LENGTH - 1)
        assert contains_identifiable_sequences(seq) is False

    def test_embedded_in_text(self):
        """Long sequence embedded in surrounding text should still be detected."""
        text = f"The patient sequence is {'ATCG' * 20} from the biopsy sample."
        assert contains_identifiable_sequences(text) is True

    def test_normal_text_ok(self):
        """Normal experimental description should not be flagged."""
        text = "We are targeting TP53 in HEK293T cells using SpCas9"
        assert contains_identifiable_sequences(text) is False

    def test_mixed_case_sequence(self):
        """Mixed case nucleotide sequences should be detected."""
        seq = "atcgATCG" * 10  # 80 chars
        assert contains_identifiable_sequences(seq) is True

    def test_rna_sequence_detected(self):
        """RNA sequences (with U) should also be detected."""
        seq = "AUGCAUGCAUGC" * 5  # 60 chars
        assert contains_identifiable_sequences(seq) is True


class TestWarningMessage:
    def test_warning_mentions_nih(self):
        assert "NIH" in WARNING_PRIVACY

    def test_warning_mentions_privacy(self):
        assert "privacy" in WARNING_PRIVACY.lower()
