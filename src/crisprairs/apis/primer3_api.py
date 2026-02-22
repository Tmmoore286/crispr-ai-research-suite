"""Primer3 integration used to design validation primer pairs."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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


@dataclass(frozen=True)
class _TargetSpec:
    template: str
    start: int
    length: int


def check_available() -> bool:
    """True when `primer3` can be imported."""
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
    """Return primer candidate dictionaries from Primer3 output."""
    if not check_available():
        logger.warning("primer3-py not installed. Install with: pip install primer3-py")
        return []

    import primer3

    target = _TargetSpec(
        template=target_sequence,
        start=target_start,
        length=target_length,
    )

    seq_args = {
        "SEQUENCE_TEMPLATE": target.template,
        "SEQUENCE_TARGET": [target.start, target.length],
    }
    global_args = dict(DEFAULT_PARAMS)
    global_args["PRIMER_NUM_RETURN"] = num_return

    try:
        raw = primer3.design_primers(seq_args, global_args)
    except Exception as exc:
        logger.error("Primer3 design failed: %s", exc)
        return []

    return _parse_primer3_result(raw)


def _parse_primer3_result(raw: dict) -> list[dict]:
    total = int(raw.get("PRIMER_PAIR_NUM_RETURNED", 0) or 0)
    output = []

    for idx in range(total):
        output.append(
            {
                "forward_seq": raw.get(f"PRIMER_LEFT_{idx}_SEQUENCE", ""),
                "forward_tm": round(float(raw.get(f"PRIMER_LEFT_{idx}_TM", 0) or 0), 1),
                "forward_gc": round(float(raw.get(f"PRIMER_LEFT_{idx}_GC_PERCENT", 0) or 0), 1),
                "reverse_seq": raw.get(f"PRIMER_RIGHT_{idx}_SEQUENCE", ""),
                "reverse_tm": round(float(raw.get(f"PRIMER_RIGHT_{idx}_TM", 0) or 0), 1),
                "reverse_gc": round(float(raw.get(f"PRIMER_RIGHT_{idx}_GC_PERCENT", 0) or 0), 1),
                "product_size": int(raw.get(f"PRIMER_PAIR_{idx}_PRODUCT_SIZE", 0) or 0),
            }
        )

    return output
