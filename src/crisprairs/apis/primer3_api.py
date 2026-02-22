"""Primer3 wrapper for designing PCR validation primers."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Default Primer3 design parameters for CRISPR validation
DEFAULT_PARAMS = {
    "PRIMER_OPT_SIZE": 20,
    "PRIMER_MIN_SIZE": 18,
    "PRIMER_MAX_SIZE": 25,
    "PRIMER_OPT_TM": 60.0,
    "PRIMER_MIN_TM": 57.0,
    "PRIMER_MAX_TM": 63.0,
    "PRIMER_MIN_GC": 40.0,
    "PRIMER_MAX_GC": 60.0,
    "PRIMER_PRODUCT_SIZE_RANGE": [[200, 500]],
    "PRIMER_NUM_RETURN": 3,
}


def check_available() -> bool:
    """Return True if primer3-py is installed and importable."""
    try:
        import primer3  # noqa: F401
        return True
    except ImportError:
        return False


def design_primers(
    target_sequence: str,
    target_start: int,
    target_length: int,
    num_return: int = 3,
) -> list[dict]:
    """Design PCR primers flanking a CRISPR target region.

    Args:
        target_sequence: Full genomic sequence containing the target.
        target_start: 0-based start position of the CRISPR target.
        target_length: Length of the CRISPR target region (typically 20-23 bp).
        num_return: Number of primer pairs to return.

    Returns:
        List of dicts with: forward_seq, forward_tm, forward_gc,
        reverse_seq, reverse_tm, reverse_gc, product_size.
        Empty list if primer3-py is not installed.
    """
    if not check_available():
        logger.warning("primer3-py not installed. Install with: pip install primer3-py")
        return []

    import primer3

    seq_args = {
        "SEQUENCE_TEMPLATE": target_sequence,
        "SEQUENCE_TARGET": [target_start, target_length],
    }

    global_args = dict(DEFAULT_PARAMS)
    global_args["PRIMER_NUM_RETURN"] = num_return

    try:
        results = primer3.design_primers(seq_args, global_args)
    except Exception as e:
        logger.error("Primer3 design failed: %s", e)
        return []

    pairs = []
    count = results.get("PRIMER_PAIR_NUM_RETURNED", 0)
    for i in range(count):
        pairs.append({
            "forward_seq": results.get(f"PRIMER_LEFT_{i}_SEQUENCE", ""),
            "forward_tm": round(results.get(f"PRIMER_LEFT_{i}_TM", 0), 1),
            "forward_gc": round(results.get(f"PRIMER_LEFT_{i}_GC_PERCENT", 0), 1),
            "reverse_seq": results.get(f"PRIMER_RIGHT_{i}_SEQUENCE", ""),
            "reverse_tm": round(results.get(f"PRIMER_RIGHT_{i}_TM", 0), 1),
            "reverse_gc": round(results.get(f"PRIMER_RIGHT_{i}_GC_PERCENT", 0), 1),
            "product_size": results.get(f"PRIMER_PAIR_{i}_PRODUCT_SIZE", 0),
        })

    return pairs
