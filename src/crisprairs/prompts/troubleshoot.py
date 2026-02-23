"""Troubleshooting prompts and knowledge map for failed CRISPR experiments."""

PROMPT_REQUEST_TROUBLESHOOT_ENTRY = """Troubleshooting intake

Tell me what failed or underperformed.
Reply with a number (1-5) or a plain-language description.

1. low/no editing
2. high toxicity
3. off-target concern
4. unexpected phenotype
5. other

Example replies:
- "1"
- "Low editing in HEK293T after lipofection"
"""

PROMPT_PROCESS_TROUBLESHOOT_ENTRY = """Classify the user's issue into one category.

Categories:
- low_efficiency
- high_toxicity
- off_target
- unexpected_phenotype
- other

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Category": "<category>",
"Summary": "<one-line summary>"
}}"""

PROMPT_REQUEST_TROUBLESHOOT_DIAGNOSE = """Please provide as many of the following as available:
- cell model
- delivery method
- CRISPR system and format
- guide details
- measured delivery/editing efficiency
- assay timepoint
"""

PROMPT_PROCESS_TROUBLESHOOT_DIAGNOSE = """Generate a differential diagnosis for the issue.

Category: {category}
Summary: {summary}

User details:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief analysis>",
"Diagnosis": [
    {{
        "cause": "<suspected cause>",
        "probability": "<high|medium|low>",
        "explanation": "<why this fits>"
    }}
],
"Key_Question": "<most important missing-data question>"
}}"""

TROUBLESHOOT_KNOWLEDGE = {
    "low_efficiency": {
        "common_causes": [
            "Guide activity is weak for the chosen locus",
            "Delivery conditions are suboptimal for the cell model",
            "Cas/editor expression or RNP quality is insufficient",
            "Target chromatin accessibility limits cutting/editing",
            "PAM or target sequence assumptions are incorrect",
            "Analysis timing is too early or too late",
        ],
        "quick_checks": [
            "Run a positive-control guide in parallel",
            "Measure delivery rate with a reporter",
            "Verify nuclease/editor presence in cells",
            "Test additional guides near the same locus",
            "Re-check PAM placement and strand assumptions",
        ],
    },
    "high_toxicity": {
        "common_causes": [
            "Delivery dose or physical parameters are too aggressive",
            "Innate stress response to payload chemistry",
            "Targeting an essential gene or pathway",
            "Excessive editor exposure duration",
            "Reagent quality issues (for example contamination)",
        ],
        "quick_checks": [
            "Reduce payload/reagent amount or pulse intensity",
            "Compare against non-targeting control",
            "Switch to more transient delivery format",
            "Check reagent quality and prep freshness",
            "Track viability at multiple post-delivery timepoints",
        ],
    },
    "off_target": {
        "common_causes": [
            "Guide sequence has poor specificity landscape",
            "Exposure window is long due to persistent expression",
            "Nuclease variant is permissive at mismatched sites",
            "Bulge/variant-aware liabilities were not screened",
        ],
        "quick_checks": [
            "Re-score guides with independent tools",
            "Use a higher-fidelity nuclease variant",
            "Shorten exposure with transient delivery",
            "Escalate to unbiased or variant-aware profiling",
        ],
    },
    "unexpected_phenotype": {
        "common_causes": [
            "Editing occurred but not in the intended functional frame",
            "Mixed populations mask the expected phenotype",
            "Compensatory biology obscures direct effect",
            "Target definition/coordinates are incorrect",
            "Baseline genotype of the model confounds interpretation",
        ],
        "quick_checks": [
            "Sequence amplicons to confirm exact edit outcomes",
            "Validate at protein level, not just DNA",
            "Subclone for genotype-homogeneous lines",
            "Confirm target coordinates and transcript model",
            "Review baseline model annotations",
        ],
    },
    "other": {
        "common_causes": [
            "Protocol drift across runs",
            "Consumable or reagent quality drift",
            "Cell model instability or misidentification",
        ],
        "quick_checks": [
            "Repeat with fresh key reagents",
            "Audit each protocol step against a reference run",
            "Confirm cell identity and contamination status",
        ],
    },
}

PROMPT_PROCESS_TROUBLESHOOT_ADVISE = """Create a prioritized corrective plan
using the diagnosis and knowledge snippets.

Category: {category}
Summary: {summary}
Details: {details}
Diagnosis: {diagnosis}
Common causes: {common_causes}
Quick checks: {quick_checks}

Return JSON only:
{{
"Thoughts": "<brief synthesis>",
"Actions": [
    {{
        "priority": <integer>,
        "action": "<specific next step>",
        "rationale": "<why it helps>",
        "difficulty": "<easy|medium|hard>",
        "expected_impact": "<high|medium|low>"
    }}
],
"Summary": "<short plan summary>"
}}"""
