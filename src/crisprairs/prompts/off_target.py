"""Prompts for standalone off-target risk assessment."""

PROMPT_REQUEST_ENTRY = """Off-target assessment mode

I can parse your guides, score specificity, and summarize risk posture.
Optionally, I can also point you to deeper genome-wide tooling.
"""

PROMPT_REQUEST_INPUT = """
Provide:
1. one or more guide sequences (20 nt spacers, no PAM)
2. species
3. nuclease/Cas system

Free-form input is accepted.
"""

PROMPT_PROCESS_INPUT = """Extract guide set and analysis context from the user message.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief analysis>",
"guides": [
    {{"sequence": "<guide>", "name": "<optional name>"}}
],
"species": "<human|mouse|rat|zebrafish|drosophila>",
"cas_system": "<SpCas9|SaCas9|enCas12a|SpRYCas9>",
"pam": "<pam string>"
}}"""

PROMPT_RISK_ASSESSMENT = """Review the scoring payload and produce a concise risk summary.

Scoring data:
{scoring_data}

Context:
{genomic_context}

Risk guideline:
- low: MIT specificity >80 and off-target count <10
- medium: MIT specificity 50-80 or off-target count 10-100
- high: MIT specificity <50 or off-target count >100

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"assessments": [
    {{
        "guide_name": "<name>",
        "sequence": "<sequence>",
        "risk_level": "<low|medium|high>",
        "explanation": "<short explanation>",
        "recommendation": "<proceed|proceed with caution|consider alternatives>"
    }}
],
"overall_recommendation": "<summary recommendation>"
}}"""

PROMPT_REQUEST_REPORT = """
Off-target scoring is complete.
Would you like setup guidance for a deeper genome-wide pass with CRISPRitz?
"""

PROMPT_PROCESS_REPORT = """Interpret whether the user wants CRISPRitz follow-up instructions.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Choice": "<yes|no>"
}}"""
