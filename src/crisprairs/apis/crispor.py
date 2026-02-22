"""CRISPOR API client for guide RNA design and scoring.

CRISPOR (crispor.tefor.net) provides guide scoring using the MIT specificity
score, Doench 2016 on-target score, and off-target prediction.
"""

from __future__ import annotations

import csv
import io
import logging

import requests

logger = logging.getLogger(__name__)

API_URL = "http://crispor.tefor.net/crispor.py"
TIMEOUT = 30  # seconds (CRISPOR can be slow)

# Common species → CRISPOR genome build
GENOME_BUILDS = {
    "human": "hg38",
    "mouse": "mm10",
    "rat": "rn6",
    "zebrafish": "danRer11",
    "drosophila": "dm6",
    "c. elegans": "ce11",
}


def genome_for_species(species: str) -> str:
    """Map a common species name to the CRISPOR genome build."""
    return GENOME_BUILDS.get(species.lower(), species)


def design_guides(
    sequence: str,
    species: str = "human",
    pam: str = "NGG",
) -> list[dict]:
    """Submit a target sequence to CRISPOR and retrieve scored guides.

    Args:
        sequence: Genomic target sequence (100-1000 bp recommended).
        species: Common species name or CRISPOR genome build.
        pam: PAM sequence (default "NGG" for SpCas9).

    Returns:
        List of guide dicts with: guide_sequence, pam, position,
        mit_specificity_score, doench2016_score, off_target_count.
        Empty list on failure.
    """
    genome = genome_for_species(species)

    try:
        resp = requests.get(
            API_URL,
            params={
                "seq": sequence,
                "org": genome,
                "pam": pam,
                "sortBy": "spec",
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return _parse_response(resp.text)

    except requests.Timeout:
        logger.warning("CRISPOR request timed out for sequence (len=%d)", len(sequence))
        return []
    except requests.RequestException as e:
        logger.error("CRISPOR API error: %s", e)
        return []


def score_existing_guides(
    guide_sequences: list[str],
    species: str = "human",
    pam: str = "NGG",
) -> list[dict]:
    """Score a list of pre-designed guide sequences.

    Submits each guide individually to CRISPOR for scoring.

    Args:
        guide_sequences: List of 20bp guide sequences (without PAM).
        species: Common species name.
        pam: PAM sequence.

    Returns:
        List of scoring result dicts per guide.
    """
    results = []
    for seq in guide_sequences:
        try:
            guides = design_guides(seq, species=species, pam=pam)
            results.append({
                "query_sequence": seq,
                "guides": guides,
            })
        except Exception as e:
            logger.error("CRISPOR scoring failed for %s: %s", seq[:10], e)
            results.append({
                "query_sequence": seq,
                "error": str(e),
                "guides": [],
            })
    return results


def is_available() -> bool:
    """Check if the CRISPOR API is reachable."""
    try:
        resp = requests.get(API_URL, timeout=5)
        return resp.status_code < 500
    except requests.RequestException:
        return False


def _parse_response(text: str) -> list[dict]:
    """Parse CRISPOR tab-delimited response into guide dicts."""
    guides = []
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter="\t")
        for row in reader:
            guides.append({
                "guide_sequence": row.get("guideSeq", ""),
                "pam": row.get("pam", ""),
                "position": row.get("position", ""),
                "mit_specificity_score": _to_float(row.get("mitSpecScore")),
                "doench2016_score": _to_float(row.get("doench2016Score")),
                "moreno_mateos_score": _to_float(row.get("morenoMateosScore")),
                "off_target_count": _to_int(row.get("offtargetCount")),
            })
    except Exception as e:
        logger.error("CRISPOR response parse error: %s", e)
    return guides


def _to_float(val) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _to_int(val) -> int | None:
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
