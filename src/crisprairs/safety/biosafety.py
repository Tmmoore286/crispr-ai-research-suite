"""Biosafety checks based on NIH Guidelines and WHO Laboratory Biosafety Manual.

Checks for:
- Human germline editing keywords (NIH Guidelines Section III-C)
- Federal Select Agents and Toxins (7 CFR 331, 9 CFR 121, 42 CFR 73)
- Dual-use research of concern (DURC) indicators (USG DURC Policy 2024)
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# Human germline editing indicators — based on NIH Guidelines Section III-C
# and the 2023 Third International Summit on Human Genome Editing
GERMLINE_KEYWORDS = frozenset({
    "embryo editing",
    "germline editing",
    "germline modification",
    "heritable editing",
    "heritable genome editing",
    "human embryo",
    "human germ cell",
    "human germline",
    "human oocyte",
    "human sperm",
    "reproductive cloning",
    "zygote editing",
})

# Federal Select Agents and Toxins (partial list) — 42 CFR Part 73
# Source: Federal Select Agent Program (selectagents.gov)
SELECT_AGENTS = frozenset({
    "bacillus anthracis",
    "bacillus cereus biovar anthracis",
    "botulinum neurotoxin",
    "brucella abortus",
    "brucella melitensis",
    "brucella suis",
    "burkholderia mallei",
    "burkholderia pseudomallei",
    "clostridium botulinum",
    "coxiella burnetii",
    "ebola virus",
    "francisella tularensis",
    "marburg virus",
    "nipah virus",
    "reconstructed 1918 influenza",
    "ricin",
    "rickettsia prowazekii",
    "sars-cov",
    "staphylococcal enterotoxin",
    "variola major virus",
    "variola minor virus",
    "yersinia pestis",
})

# Dual-use research of concern (DURC) indicators — USG DURC Policy
DURC_KEYWORDS = frozenset({
    "enhance transmissibility",
    "enhance virulence",
    "evasion of countermeasures",
    "gain of function",
    "immune evasion",
    "pandemic potential",
    "pathogen enhancement",
    "resistance to therapeutics",
    "weaponization",
})


class BiosafetyFlag:
    """Represents a biosafety concern flagged during screening."""

    def __init__(self, category: str, trigger: str, message: str):
        self.category = category  # "germline", "select_agent", "dual_use"
        self.trigger = trigger    # the matched keyword
        self.message = message    # human-readable explanation


def check_biosafety(text: str) -> list[BiosafetyFlag]:
    """Screen text for biosafety concerns.

    Checks user input and LLM prompts against known biosafety indicators.
    Returns a list of BiosafetyFlag objects (empty if no concerns).

    Args:
        text: Text to screen (user input, prompt, gene name, etc.)

    Returns:
        List of BiosafetyFlag instances. Empty means no concerns detected.
    """
    text_lower = text.lower()
    flags: list[BiosafetyFlag] = []

    # Check germline keywords
    for keyword in GERMLINE_KEYWORDS:
        if keyword in text_lower:
            flags.append(BiosafetyFlag(
                category="germline",
                trigger=keyword,
                message=(
                    f"Germline editing indicator detected: '{keyword}'. "
                    "Human germline editing raises significant ethical and regulatory concerns. "
                    "See NIH Guidelines Section III-C and the Third International Summit "
                    "on Human Genome Editing (2023)."
                ),
            ))

    # Check select agents
    for agent in SELECT_AGENTS:
        if agent in text_lower:
            flags.append(BiosafetyFlag(
                category="select_agent",
                trigger=agent,
                message=(
                    f"Federal Select Agent detected: '{agent}'. "
                    "Work with select agents requires registration with the Federal "
                    "Select Agent Program (42 CFR Part 73). Ensure proper BSL facility "
                    "and IBC approval before proceeding."
                ),
            ))

    # Check DURC keywords
    for keyword in DURC_KEYWORDS:
        if keyword in text_lower:
            flags.append(BiosafetyFlag(
                category="dual_use",
                trigger=keyword,
                message=(
                    f"Dual-use research concern detected: '{keyword}'. "
                    "This research may fall under the USG Policy for Oversight of "
                    "Dual Use Research of Concern. Consult your Institutional Review "
                    "Entity (IRE) and IBC before proceeding."
                ),
            ))

    if flags:
        logger.warning(
            "Biosafety concerns detected: %s",
            [f.trigger for f in flags],
        )

    return flags


def has_biosafety_concerns(text: str) -> bool:
    """Quick check: does the text trigger any biosafety flags?"""
    return len(check_biosafety(text)) > 0


def format_biosafety_warnings(flags: list[BiosafetyFlag]) -> str:
    """Format biosafety flags as a user-facing warning message."""
    if not flags:
        return ""
    lines = ["**Biosafety Review Required**", ""]
    for flag in flags:
        lines.append(f"- **[{flag.category.upper()}]** {flag.message}")
    lines.append("")
    lines.append(
        "Please consult your Institutional Biosafety Committee (IBC) "
        "before proceeding with this experiment."
    )
    return "\n".join(lines)
