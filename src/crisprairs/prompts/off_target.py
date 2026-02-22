"""Prompt templates for the off-target analysis agent."""

PROMPT_REQUEST_ENTRY = """Now, let's analyze off-target effects for your CRISPR guide RNAs.

**Off-target editing** occurs when your guide RNA directs Cas
nuclease to unintended genomic sites with similar sequences.
This is a critical safety concern, especially for therapeutic
applications.

This agent will:
1. Accept your guide RNA sequence(s)
2. Score each guide for specificity using CRISPOR
3. Annotate potential off-target sites with genomic context
4. Generate a structured risk assessment report
5. Optionally guide you through deep genome-wide analysis with CRISPRitz
"""

PROMPT_REQUEST_INPUT = """Please provide:

1. **Guide RNA sequence(s)** — 20 nt spacer sequences (without PAM), one per line
2. **Species** — human, mouse, rat, zebrafish, or drosophila
3. **Cas system** — SpCas9 (NGG), SaCas9 (NNGRRT), enCas12a (TTTV), or specify PAM

Example:
```
AGCTTAGCTAGCTAGCTAGC
GCTAGCTAGCTAGCTAGCTA
Species: human
Cas system: SpCas9
```

Or simply describe what you need and I will extract the details.
"""

PROMPT_PROCESS_INPUT = """Please act as an expert in CRISPR
off-target analysis. Given the user input, extract the guide
RNA sequences and parameters. Please format your response and
make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<step-by-step analysis of the input>",
"guides": [
    {{"sequence": "<20nt DNA sequence>", "name": "<optional label or sgRNA-1>"}}
],
"species": "<human|mouse|rat|zebrafish|drosophila>",
"cas_system": "<SpCas9|SaCas9|enCas12a|SpRYCas9>",
"pam": "<NGG|NNGRRT|TTTV|NNN>"
}}"""

PROMPT_RISK_ASSESSMENT = """Please act as an expert in CRISPR
off-target analysis and safety assessment. Given the following
off-target scoring data for guide RNAs, generate a risk
assessment.

Scoring data:
{scoring_data}

Genomic context:
{genomic_context}

For each guide, assign a risk level (low, medium, high) based on:
- MIT specificity score > 80 and off-target count < 10 -> low risk
- MIT specificity score 50-80 or off-target count 10-100 -> medium risk
- MIT specificity score < 50 or off-target count > 100 -> high risk

Response format (JSON parsable):
{{
"Thoughts": "<analysis reasoning>",
"assessments": [
    {{
        "guide_name": "<name>",
        "sequence": "<sequence>",
        "risk_level": "<low|medium|high>",
        "explanation": "<1-2 sentence explanation>",
        "recommendation": "<proceed|proceed with caution|consider alternatives>"
    }}
],
"overall_recommendation": "<summary recommendation for the experiment>"
}}"""

PROMPT_REQUEST_REPORT = """
**Off-Target Analysis Complete.**

Would you like instructions for deep genome-wide off-target
analysis using CRISPRitz? This uses a more thorough search
algorithm that accounts for DNA/RNA bulges and can incorporate
genetic variants.
"""

PROMPT_PROCESS_REPORT = """Please act as an expert in CRISPR
technology. Given the user input, determine if they want
CRISPRitz instructions for deep off-target analysis. Please
format your response and make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Choice": "<yes|no>"
}}"""
