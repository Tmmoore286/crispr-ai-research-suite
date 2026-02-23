#!/usr/bin/env python3
"""Scheduled health checks for external CRISPR data sources and local tooling."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass

import requests

from crisprairs.apis.blast import BLAST_API_URL, ORGANISM_MAP
from crisprairs.apis.crispor import API_URL as CRISPOR_API_URL
from crisprairs.apis.crispor import GENOME_BUILDS
from crisprairs.apis.crispor import is_available as crispor_is_available
from crisprairs.apis.ensembl import BASE_URL as ENSEMBL_API_URL
from crisprairs.apis.ensembl import SPECIES_MAP
from crisprairs.apis.ncbi import SPECIES_TAXID
from crisprairs.apis.primer3_api import check_available as primer3_available

DEFAULT_TIMEOUT = 10
CORE_SPECIES = {"human", "mouse", "rat", "zebrafish", "drosophila"}


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    details: str
    latency_ms: int


def check_species_mappings() -> tuple[bool, str]:
    """Ensure core species coverage is present across integration maps."""
    maps = {
        "ensembl": SPECIES_MAP,
        "crispor": GENOME_BUILDS,
        "ncbi_taxid": SPECIES_TAXID,
        "blast_organism": ORGANISM_MAP,
    }
    missing: dict[str, list[str]] = {}
    blank_values: dict[str, list[str]] = {}

    for name, mapping in maps.items():
        keys = set(mapping.keys())
        missing_keys = sorted(CORE_SPECIES - keys)
        if missing_keys:
            missing[name] = missing_keys
        blanks = [k for k, v in mapping.items() if not str(v).strip()]
        if blanks:
            blank_values[name] = sorted(blanks)

    if missing or blank_values:
        return (
            False,
            json.dumps({"missing_core_species": missing, "blank_values": blank_values}),
        )
    return (True, "core species mappings are present and non-empty")


def check_primer3_runtime() -> tuple[bool, str]:
    """Verify primer3-py importability in the current environment."""
    ok = primer3_available()
    if ok:
        return (True, "primer3-py import succeeded")
    return (False, "primer3-py unavailable; install primer3-py to enable primer design")


def check_ensembl() -> tuple[bool, str]:
    """Ping Ensembl REST API."""
    resp = requests.get(
        f"{ENSEMBL_API_URL}/info/ping",
        params={"content-type": "application/json"},
        headers={"Accept": "application/json"},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("ping") == 1:
        return (True, "Ensembl ping ok")
    return (False, f"Unexpected Ensembl response: {data}")


def check_crispor() -> tuple[bool, str]:
    """Check CRISPOR API reachability."""
    if crispor_is_available():
        return (True, "CRISPOR endpoint reachable")
    return (False, f"CRISPOR endpoint unavailable: {CRISPOR_API_URL}")


def check_ncbi_eutils() -> tuple[bool, str]:
    """Check NCBI Entrez E-utilities endpoint."""
    resp = requests.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
        params={"db": "gene", "retmode": "json"},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    db_name = data.get("einforesult", {}).get("dbinfo", [{}])[0].get("dbname")
    if db_name == "gene":
        return (True, "NCBI eutils einfo ok")
    return (False, f"Unexpected NCBI einfo response: dbname={db_name}")


def check_blast() -> tuple[bool, str]:
    """Check BLAST CGI endpoint reachability."""
    resp = requests.get(
        BLAST_API_URL,
        params={"CMD": "Get"},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    if "BLAST" in resp.text.upper():
        return (True, "BLAST endpoint reachable")
    return (False, "BLAST response did not contain expected marker text")


def _run_check(name: str, fn) -> CheckResult:
    started = time.perf_counter()
    try:
        ok, details = fn()
    except Exception as exc:  # pragma: no cover - defensive wrapper
        ok = False
        details = f"{type(exc).__name__}: {exc}"
    latency_ms = int((time.perf_counter() - started) * 1000)
    return CheckResult(name=name, ok=ok, details=details, latency_ms=latency_ms)


def _print_results(results: list[CheckResult]) -> None:
    print("External Source Health Check")
    print("=" * 80)
    for res in results:
        status = "PASS" if res.ok else "FAIL"
        print(f"[{status}] {res.name} ({res.latency_ms} ms)")
        print(f"  {res.details}")
    print("=" * 80)
    passed = sum(1 for r in results if r.ok)
    print(f"Summary: {passed}/{len(results)} checks passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run external source health checks for Ensembl, CRISPOR, NCBI, BLAST, "
            "species mappings, and primer3 runtime."
        )
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Skip network checks and only run local consistency/runtime checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    results = [
        _run_check("species_mappings", check_species_mappings),
        _run_check("primer3_runtime", check_primer3_runtime),
    ]
    if not args.skip_network:
        results.extend(
            [
                _run_check("ensembl_api", check_ensembl),
                _run_check("crispor_api", check_crispor),
                _run_check("ncbi_eutils_api", check_ncbi_eutils),
                _run_check("ncbi_blast_api", check_blast),
            ]
        )

    _print_results(results)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
