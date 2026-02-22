"""Sequence privacy checks for identifiable genomic data.

Detects potentially identifiable human genomic sequences in user input
to prevent inadvertent disclosure of patient data through LLM prompts.

Based on NIH Genomic Data Sharing Policy (GDS Policy, NOT-OD-14-124)
and the principle that sufficiently long, unique sequences can be used
to re-identify individuals.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Minimum length of a contiguous nucleotide sequence considered potentially
# identifiable. Short sequences (e.g., 20-nt guide RNAs) are not unique to
# individuals, but longer stretches (>50 nt) may be. This threshold is
# conservative.
MIN_IDENTIFIABLE_LENGTH = 50

# Pattern matching nucleotide sequences (DNA/RNA)
_NUCLEOTIDE_PATTERN = re.compile(r"[ACGTUacgtu]{" + str(MIN_IDENTIFIABLE_LENGTH) + r",}")

WARNING_PRIVACY = (
    "The input appears to contain a long nucleotide sequence (>50 bases) that could "
    "potentially be used to identify an individual. To protect patient privacy, please "
    "remove patient-derived sequences or use anonymized reference sequences instead. "
    "See NIH Genomic Data Sharing Policy (NOT-OD-14-124)."
)


def contains_identifiable_sequences(text: str) -> bool:
    """Check if text contains potentially identifiable genomic sequences.

    A sequence of 50+ contiguous nucleotide characters is considered
    potentially identifiable. This is a conservative heuristic — short
    guide RNA sequences (20 nt) are fine, but long genomic stretches
    could fingerprint an individual.

    Args:
        text: Any text that might contain genomic sequences.

    Returns:
        True if a potentially identifiable sequence is found.
    """
    matches = _NUCLEOTIDE_PATTERN.findall(text)
    if matches:
        logger.warning(
            "Potentially identifiable sequence detected (%d chars)",
            len(matches[0]),
        )
        return True
    return False
