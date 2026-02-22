"""Thin client for NCBI BLAST used in primer specificity checks."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

BLAST_API_URL = "https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi"
DEFAULT_TIMEOUT = 10
DEFAULT_POLL_INTERVAL = 5
DEFAULT_MAX_WAIT = 60

ORGANISM_MAP = {
    "human": "Homo sapiens",
    "mouse": "Mus musculus",
    "rat": "Rattus norvegicus",
    "zebrafish": "Danio rerio",
    "drosophila": "Drosophila melanogaster",
}


@dataclass(frozen=True)
class _BlastJob:
    rid: str


def submit_blast(
    sequence: str,
    database: str = "nt",
    program: str = "blastn",
    organism: str | None = None,
) -> str | None:
    """Submit one nucleotide query to BLAST and return the RID."""
    payload = _submission_payload(
        sequence=sequence,
        database=database,
        program=program,
        organism=organism,
    )

    try:
        response = requests.post(BLAST_API_URL, data=payload, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except Exception as exc:
        logger.error("BLAST submission failed: %s", exc)
        return None

    rid = _extract_rid(response.text)
    if rid is None:
        logger.error("No RID found in BLAST submission response")
    return rid


def poll_results(
    rid: str,
    max_wait: int = DEFAULT_MAX_WAIT,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> list[dict]:
    """Poll BLAST for a finished result set and return parsed hits."""
    job = _BlastJob(rid=rid)
    started = time.time()

    while (time.time() - started) < max_wait:
        try:
            response = requests.get(
                BLAST_API_URL,
                params={"CMD": "Get", "RID": job.rid, "FORMAT_TYPE": "XML"},
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("BLAST poll error: %s", exc)
            return []

        state = _job_state(response.text)
        if state == "WAITING":
            time.sleep(poll_interval)
            continue
        if state == "FAILED":
            logger.error("BLAST job failed")
            return []
        if state == "UNKNOWN":
            logger.error("BLAST job not found (RID may have expired)")
            return []

        return _parse_blast_xml(response.text)

    logger.warning("BLAST timed out after %ds for RID %s", max_wait, job.rid)
    return []


def check_primer_specificity(
    forward: str,
    reverse: str,
    organism: str | None = None,
) -> dict:
    """Run BLAST checks for both primers and report a compact specificity summary."""
    result = {
        "specific": False,
        "forward_hits": 0,
        "reverse_hits": 0,
        "forward_results": [],
        "reverse_results": [],
    }

    forward_rid = submit_blast(forward, organism=organism)
    reverse_rid = submit_blast(reverse, organism=organism)

    if forward_rid:
        f_hits = poll_results(forward_rid)
        result["forward_hits"] = len(f_hits)
        result["forward_results"] = f_hits[:5]

    if reverse_rid:
        r_hits = poll_results(reverse_rid)
        result["reverse_hits"] = len(r_hits)
        result["reverse_results"] = r_hits[:5]

    both_submitted = forward_rid is not None and reverse_rid is not None
    result["specific"] = (
        both_submitted
        and result["forward_hits"] == 1
        and result["reverse_hits"] == 1
    )
    return result


def _parse_blast_xml(xml_text: str) -> list[dict]:
    """Parse BLAST XML and return first-HSP hit summaries."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        logger.error("Failed to parse BLAST XML response")
        return []

    parsed: list[dict] = []
    for hit in root.iter("Hit"):
        row = {
            "accession": _get_text(hit, "Hit_accession"),
            "title": _get_text(hit, "Hit_def"),
            "length": _get_text(hit, "Hit_len"),
        }
        first_hsp = next(hit.iter("Hsp"), None)
        if first_hsp is not None:
            row["identity"] = _get_text(first_hsp, "Hsp_identity")
            row["align_len"] = _get_text(first_hsp, "Hsp_align-len")
            row["e_value"] = _get_text(first_hsp, "Hsp_evalue")
            row["bit_score"] = _get_text(first_hsp, "Hsp_bit-score")
        parsed.append(row)
    return parsed


def _submission_payload(
    sequence: str,
    database: str,
    program: str,
    organism: str | None,
) -> dict[str, str]:
    payload = {
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
        payload["ENTREZ_QUERY"] = f'"{org_name}"[ORGN]'
    return payload


def _extract_rid(text: str) -> str | None:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("RID ="):
            return line.split("=", 1)[1].strip()
    return None


def _job_state(text: str) -> str | None:
    if "Status=WAITING" in text:
        return "WAITING"
    if "Status=FAILED" in text:
        return "FAILED"
    if "Status=UNKNOWN" in text:
        return "UNKNOWN"
    return None


def _get_text(element, tag: str) -> str:
    node = element.find(tag)
    if node is None or node.text is None:
        return ""
    return node.text
