"""NCBI gene lookup via Biopython Bio.Entrez.

Uses Biopython's Entrez module for structured access to NCBI E-utilities.
Requires NCBI_EMAIL env var for polite API usage.
"""

from __future__ import annotations

import logging
import os

import dotenv

dotenv.load_dotenv()
logger = logging.getLogger(__name__)

# Species name → NCBI taxonomy ID mapping
SPECIES_TAXID = {
    "human": "9606",
    "mouse": "10090",
    "rat": "10116",
    "zebrafish": "7955",
    "drosophila": "7227",
    "c. elegans": "6239",
}


def _configure_entrez():
    """Configure Biopython Entrez with email and optional API key."""
    from Bio import Entrez

    Entrez.email = os.getenv("NCBI_EMAIL", "anonymous@example.com")
    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        Entrez.api_key = api_key
    return Entrez


def fetch_gene_info(gene_symbol: str, species: str = "human") -> dict | None:
    """Look up gene information from NCBI via Biopython Entrez.

    Args:
        gene_symbol: Gene symbol (e.g. "TP53", "BRCA1").
        species: Common species name (e.g. "human", "mouse").

    Returns:
        Dict with gene_id, symbol, full_name, chromosome, organism,
        aliases, summary, genomic_info. None on failure.
    """
    try:
        Entrez = _configure_entrez()

        taxid = SPECIES_TAXID.get(species.lower(), "")
        query = f"{gene_symbol}[Gene Name]"
        if taxid:
            query += f" AND {taxid}[Taxonomy ID]"

        # Search for gene ID
        with Entrez.esearch(db="gene", term=query, retmax=1) as handle:
            search_results = Entrez.read(handle)

        id_list = search_results.get("IdList", [])
        if not id_list:
            logger.warning("No NCBI gene found for %s (%s)", gene_symbol, species)
            return None

        gene_id = id_list[0]

        # Fetch gene summary
        with Entrez.esummary(db="gene", id=gene_id, retmode="json") as handle:
            import json
            summary_data = json.loads(handle.read())

        result = summary_data.get("result", {}).get(str(gene_id), {})

        return {
            "gene_id": gene_id,
            "symbol": result.get("name", gene_symbol),
            "full_name": result.get("description", ""),
            "chromosome": result.get("chromosome", ""),
            "organism": result.get("organism", {}).get("scientificname", species),
            "aliases": result.get("otheraliases", ""),
            "summary": result.get("summary", ""),
            "genomic_info": result.get("genomicinfo", []),
        }

    except ImportError:
        logger.error("Biopython is required: pip install biopython")
        return None
    except Exception as e:
        logger.error("NCBI Entrez error for %s: %s", gene_symbol, e)
        return None


def fetch_gene_sequence(gene_id: str, seq_type: str = "genomic") -> str | None:
    """Fetch nucleotide sequence for a gene via Entrez efetch.

    Args:
        gene_id: NCBI Gene ID.
        seq_type: Sequence type.

    Returns:
        Sequence string or None on failure.
    """
    try:
        Entrez = _configure_entrez()

        with Entrez.efetch(
            db="nucleotide", id=gene_id, rettype="fasta", retmode="text"
        ) as handle:
            from Bio import SeqIO
            record = SeqIO.read(handle, "fasta")
            return str(record.seq)

    except ImportError:
        logger.error("Biopython is required: pip install biopython")
        return None
    except Exception as e:
        logger.error("NCBI sequence fetch error for %s: %s", gene_id, e)
        return None
