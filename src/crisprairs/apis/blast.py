"""NCBI BLAST REST API client for primer specificity verification."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)

BLAST_API_URL = "https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi"
DEFAULT_TIMEOUT = 10  # seconds per HTTP request
DEFAULT_POLL_INTERVAL = 5  # seconds between status checks
DEFAULT_MAX_WAIT = 60  # seconds total wait for results

# Map common species to NCBI organism names
ORGANISM_MAP = {
    "human": "Homo sapiens",
    "mouse": "Mus musculus",
    "rat": "Rattus norvegicus",
    "zebrafish": "Danio rerio",
    "drosophila": "Drosophila melanogaster",
}


def submit_blast(
    sequence: str,
    database: str = "nt",
    program: str = "blastn",
    organism: str | None = None,
) -> str | None:
    """Submit a BLAST query to NCBI.

    Args:
        sequence: DNA sequence to search.
        database: BLAST database (default: nt for nucleotide).
        program: BLAST program (default: blastn).
        organism: Optional organism filter (e.g., 'human', 'mouse').

    Returns:
        Request ID (RID) string, or None on failure.
    """
    params = {
        "CMD": "Put",
        "PROGRAM": program,
        "DATABASE": database,
        "QUERY": sequence,
        "FORMAT_TYPE": "XML",
        "WORD_SIZE": "7",
        "EXPECT": "10",
    }

    if organism:
        org_name = ORGANISM_MAP.get(organism.lower(), organism)
        params["ENTREZ_QUERY"] = f'"{org_name}"[ORGN]'

    try:
        resp = requests.post(BLAST_API_URL, data=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()

        for line in resp.text.split("\n"):
            if line.strip().startswith("RID ="):
                return line.split("=")[1].strip()

        logger.error("No RID found in BLAST submission response")
        return None
    except Exception as e:
        logger.error("BLAST submission failed: %s", e)
        return None


def poll_results(
    rid: str,
    max_wait: int = DEFAULT_MAX_WAIT,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> list[dict]:
    """Poll NCBI BLAST for results.

    Args:
        rid: Request ID from submit_blast.
        max_wait: Maximum seconds to wait.
        poll_interval: Seconds between status checks.

    Returns:
        List of hit dicts with accession, title, identity, e_value.
        Empty list on timeout or failure.
    """
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            resp = requests.get(
                BLAST_API_URL,
                params={"CMD": "Get", "RID": rid, "FORMAT_TYPE": "XML"},
                timeout=DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()

            if "Status=WAITING" in resp.text:
                time.sleep(poll_interval)
                continue

            if "Status=FAILED" in resp.text:
                logger.error("BLAST job failed")
                return []

            if "Status=UNKNOWN" in resp.text:
                logger.error("BLAST job not found (RID may have expired)")
                return []

            return _parse_blast_xml(resp.text)

        except requests.RequestException as e:
            logger.error("BLAST poll error: %s", e)
            return []

    logger.warning("BLAST timed out after %ds for RID %s", max_wait, rid)
    return []


def check_primer_specificity(
    forward: str,
    reverse: str,
    organism: str | None = None,
) -> dict:
    """Check primer pair specificity using BLAST.

    Args:
        forward: Forward primer sequence.
        reverse: Reverse primer sequence.
        organism: Optional organism filter.

    Returns:
        Dict with: specific (bool), forward_hits, reverse_hits,
        forward_results, reverse_results.
    """
    result = {
        "specific": False,
        "forward_hits": 0,
        "reverse_hits": 0,
        "forward_results": [],
        "reverse_results": [],
    }

    fwd_rid = submit_blast(forward, organism=organism)
    rev_rid = submit_blast(reverse, organism=organism)

    if fwd_rid:
        fwd_hits = poll_results(fwd_rid)
        result["forward_hits"] = len(fwd_hits)
        result["forward_results"] = fwd_hits[:5]

    if rev_rid:
        rev_hits = poll_results(rev_rid)
        result["reverse_hits"] = len(rev_hits)
        result["reverse_results"] = rev_hits[:5]

    both_submitted = fwd_rid is not None and rev_rid is not None
    result["specific"] = (
        both_submitted
        and result["forward_hits"] == 1
        and result["reverse_hits"] == 1
    )

    return result


def _parse_blast_xml(xml_text: str) -> list[dict]:
    """Parse BLAST XML output into a list of hit dicts."""
    hits = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        logger.error("Failed to parse BLAST XML response")
        return hits

    for hit in root.iter("Hit"):
        hit_data = {
            "accession": _get_text(hit, "Hit_accession"),
            "title": _get_text(hit, "Hit_def"),
            "length": _get_text(hit, "Hit_len"),
        }

        for hsp in hit.iter("Hsp"):
            hit_data["identity"] = _get_text(hsp, "Hsp_identity")
            hit_data["align_len"] = _get_text(hsp, "Hsp_align-len")
            hit_data["e_value"] = _get_text(hsp, "Hsp_evalue")
            hit_data["bit_score"] = _get_text(hsp, "Hsp_bit-score")
            break  # Only take the first HSP

        hits.append(hit_data)

    return hits


def _get_text(element, tag: str) -> str:
    """Get text content of a child XML element, or empty string."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text
    return ""
