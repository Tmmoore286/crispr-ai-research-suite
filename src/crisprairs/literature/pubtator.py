"""PubTator entity enrichment client."""

from __future__ import annotations

import logging
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)

PUBTATOR_API = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson"
TIMEOUT = 15


def fetch_entity_annotations(pmids: list[str]) -> dict[str, dict[str, list[str]]]:
    """Fetch PubTator annotations for PMIDs grouped by entity type."""
    clean_pmids = [str(p) for p in pmids if str(p).strip()]
    if not clean_pmids:
        return {}

    try:
        response = requests.get(
            PUBTATOR_API,
            params={"pmids": ",".join(clean_pmids)},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.error("PubTator request error: %s", exc)
        return {}
    except ValueError as exc:
        logger.error("PubTator JSON parse error: %s", exc)
        return {}

    return _parse_pubtator_bioc(payload)


def _parse_pubtator_bioc(payload) -> dict[str, dict[str, list[str]]]:
    docs = payload if isinstance(payload, list) else [payload]
    output: dict[str, dict[str, list[str]]] = {}

    for doc in docs:
        pmid = str(doc.get("id", "")).strip()
        if not pmid:
            continue
        bucket: dict[str, set[str]] = defaultdict(set)

        for passage in doc.get("passages", []):
            for annotation in passage.get("annotations", []):
                text = str(annotation.get("text", "")).strip()
                ann_type = str(annotation.get("infons", {}).get("type", "")).strip()
                if not text or not ann_type:
                    continue
                bucket[ann_type].add(text)

        output[pmid] = {k: sorted(v) for k, v in bucket.items()}
    return output
