"""Ensembl REST API client for gene, sequence, and ortholog lookups."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://rest.ensembl.org"
TIMEOUT = 10  # seconds

# Common species → Ensembl species name
SPECIES_MAP = {
    "human": "homo_sapiens",
    "mouse": "mus_musculus",
    "rat": "rattus_norvegicus",
    "zebrafish": "danio_rerio",
    "drosophila": "drosophila_melanogaster",
    "c. elegans": "caenorhabditis_elegans",
}


def _get(endpoint: str, params: dict | None = None) -> Any | None:
    """Issue a GET request to the Ensembl REST API.

    Returns parsed JSON on success, None on failure.
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error("Ensembl API error [%s]: %s", endpoint, e)
        return None


def resolve_species(species: str) -> str:
    """Resolve a common species name to the Ensembl species identifier."""
    return SPECIES_MAP.get(species.lower(), species.lower().replace(" ", "_"))


def lookup_gene_id(symbol: str, species: str = "human") -> str | None:
    """Find the Ensembl gene ID for a gene symbol.

    Args:
        symbol: Gene symbol (e.g. "TP53").
        species: Common species name.

    Returns:
        Ensembl stable gene ID (e.g. "ENSG00000141510") or None.
    """
    ensembl_sp = resolve_species(species)
    data = _get(f"/xrefs/symbol/{ensembl_sp}/{symbol}")
    if not data:
        return None
    for entry in data:
        if entry.get("type") == "gene":
            return entry.get("id")
    return data[0].get("id") if data else None


def get_gene_info(gene_id: str) -> dict | None:
    """Fetch gene metadata by Ensembl ID.

    Returns dict with id, display_name, biotype, description, start, end, strand, seq_region.
    """
    data = _get(f"/lookup/id/{gene_id}")
    if not data:
        return None
    return {
        "id": data.get("id"),
        "display_name": data.get("display_name", ""),
        "biotype": data.get("biotype", ""),
        "description": data.get("description", ""),
        "start": data.get("start"),
        "end": data.get("end"),
        "strand": data.get("strand"),
        "seq_region": data.get("seq_region_name", ""),
        "species": data.get("species", ""),
    }


def get_sequence(gene_id: str, expand_bp: int = 0) -> dict | None:
    """Fetch genomic sequence for a gene.

    Args:
        gene_id: Ensembl gene ID.
        expand_bp: Number of bases to expand on each side.

    Returns:
        Dict with id, seq_length, sequence_preview (first 500bp), description.
    """
    params: dict[str, Any] = {"type": "genomic"}
    if expand_bp:
        params["expand_5prime"] = expand_bp
        params["expand_3prime"] = expand_bp

    data = _get(f"/sequence/id/{gene_id}", params=params)
    if not data:
        return None

    seq = data.get("seq", "")
    return {
        "id": data.get("id", gene_id),
        "description": data.get("desc", ""),
        "seq_length": len(seq),
        "sequence_preview": seq[:500] + ("..." if len(seq) > 500 else ""),
        "full_sequence": seq,
    }


def list_transcripts(gene_id: str) -> list[dict]:
    """List transcript variants for a gene.

    Returns list of dicts: transcript_id, biotype, is_canonical, length.
    """
    data = _get(f"/lookup/id/{gene_id}", params={"expand": "1"})
    if not data:
        return []

    results = []
    for t in data.get("Transcript", []):
        results.append({
            "transcript_id": t.get("id", ""),
            "biotype": t.get("biotype", ""),
            "is_canonical": t.get("is_canonical", 0) == 1,
            "length": t.get("length", 0),
        })
    return results


def find_orthologs(gene_id: str) -> list[dict]:
    """Find cross-species orthologs for a gene.

    Returns list of dicts: species, gene_id, type, percent_identity.
    """
    data = _get(f"/homology/id/{gene_id}", params={"type": "orthologues"})
    if not data:
        return []

    results = []
    homology_data = data.get("data", [])
    if not homology_data:
        return []

    for hom in homology_data[0].get("homologies", []):
        target = hom.get("target", {})
        results.append({
            "species": target.get("species", ""),
            "gene_id": target.get("id", ""),
            "type": hom.get("type", ""),
            "percent_identity": target.get("perc_id", 0),
        })
    return results
