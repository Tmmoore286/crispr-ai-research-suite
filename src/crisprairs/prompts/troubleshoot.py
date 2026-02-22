"""Prompt templates for troubleshooting mode — CRISPR experiment failure diagnosis."""

PROMPT_REQUEST_TROUBLESHOOT_ENTRY = """**Troubleshooting Mode**

I can help diagnose issues with your CRISPR experiment. What problem are you experiencing?

1. Low or no editing efficiency
2. High toxicity / low cell viability
3. Off-target effects detected
4. Unexpected phenotype or no phenotype
5. Other issue (please describe)
"""

PROMPT_PROCESS_TROUBLESHOOT_ENTRY = """Please act as an expert
in CRISPR technology troubleshooting. Given the user input
describing their experimental problem, categorize the issue
into one of the following categories. Please format your
response and make sure it is parsable by JSON.

Categories:
1. low_efficiency — Low or no editing efficiency
2. high_toxicity — High toxicity or low cell viability
3. off_target — Off-target effects detected
4. unexpected_phenotype — Unexpected phenotype or no observable phenotype
5. other — Other issue

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Category": "<category>",
"Summary": "<brief summary of the user's problem>"
}}"""

PROMPT_REQUEST_TROUBLESHOOT_DIAGNOSE = """To help diagnose the
issue, please provide the following details about your
experiment:

1. **Cell type/line** used (e.g., HEK293T, K562, primary T cells)
2. **Delivery method** (e.g., lipofection, electroporation, viral transduction)
3. **CRISPR system** used (e.g., SpCas9 RNP, plasmid-based, lentiviral)
4. **Guide RNA details** (how many guides tested, any validation done?)
5. **Transfection/transduction efficiency** (if measured)
6. **Time point** of analysis after delivery

Please share whatever details you have — even partial information helps.
"""

PROMPT_PROCESS_TROUBLESHOOT_DIAGNOSE = """Please act as an
expert CRISPR troubleshooting consultant. Given the category
of the problem and the user's experimental details, analyze
the likely causes and prepare a diagnosis. Please format your
response and make sure it is parsable by JSON.

Problem category: {category}
Problem summary: {summary}

User's experimental details:

"{user_message}"

For each likely cause, rate its probability (high/medium/low) based on the user's details.

Response format:
{{
"Thoughts": "<step-by-step analysis>",
"Diagnosis": [
    {{
        "cause": "<likely cause>",
        "probability": "<high|medium|low>",
        "explanation": "<why this is likely given the user's setup>"
    }}
],
"Key_Question": "<one critical follow-up question if information is missing>"
}}"""

# Domain knowledge about common CRISPR failure modes
TROUBLESHOOT_KNOWLEDGE = {
    "low_efficiency": {
        "common_causes": [
            "Poor guide RNA design — low on-target activity score",
            "Insufficient delivery — low transfection/transduction efficiency",
            "Suboptimal Cas protein expression — promoter not active in cell type",
            "Target site accessibility — chromatin state blocking Cas access",
            "Incorrect PAM orientation or mismatch",
            "RNP degradation — nuclease/guide not forming proper complex",
            "Cell type-specific resistance to editing",
        ],
        "quick_checks": [
            "Verify transfection efficiency with a fluorescent reporter",
            "Test a validated positive-control guide in parallel",
            "Check Cas9 expression by Western blot",
            "Try multiple guides targeting different exons",
            "Test RNP delivery if using plasmid-based approach",
        ],
    },
    "high_toxicity": {
        "common_causes": [
            "DNA damage response to double-strand breaks (especially with multiple guides)",
            "Immune response to foreign DNA/RNA (innate sensing of Cas9 mRNA or plasmid)",
            "Lipofection toxicity — too much transfection reagent",
            "Electroporation conditions too harsh",
            "Essential gene targeted — editing causes cell death",
            "Off-target cutting at essential loci",
            "Contaminant in reagent preparations (endotoxin in plasmid prep)",
        ],
        "quick_checks": [
            "Reduce transfection reagent amount or electroporation voltage",
            "Use RNP delivery to reduce innate immune activation",
            "Test non-targeting control guide at same conditions",
            "Check endotoxin levels in plasmid preparations",
            "Add p53 inhibitor (if applicable) to reduce DNA damage response",
        ],
    },
    "off_target": {
        "common_causes": [
            "Guide RNA has high off-target potential — too many similar sites in genome",
            "Excess Cas protein or long expression duration",
            "Using SpCas9 without high-fidelity variant",
            "Bulge-tolerant off-targets not predicted by mismatch-only tools",
            "Cas protein variant with relaxed PAM specificity (e.g., SpRY)",
        ],
        "quick_checks": [
            "Re-check guide specificity score with multiple tools (CRISPOR, Cas-OFFinder)",
            "Switch to high-fidelity Cas9 variant (eSpCas9, HF-Cas9, HiFi Cas9)",
            "Reduce Cas9 protein/mRNA amount or shorten expression window",
            "Use RNP delivery for transient activity",
            "Perform GUIDE-seq or CIRCLE-seq for unbiased off-target detection",
        ],
    },
    "unexpected_phenotype": {
        "common_causes": [
            "In-frame deletion — knockout not achieved despite indels",
            "Genetic compensation — upregulation of paralog genes",
            "Mosaic editing — not all cells edited, mixed population",
            "Wrong gene targeted — verify gene symbol and coordinates",
            "Cell line already has mutation in target gene",
            "Non-coding region targeted — guide in intron or UTR",
        ],
        "quick_checks": [
            "Sequence the target site to confirm frameshift/premature stop",
            "Verify protein loss by Western blot, not just DNA editing",
            "Single-cell clone isolation for homogeneous populations",
            "Check gene expression databases for your cell line",
            "Verify the exact genomic coordinates of your guide",
        ],
    },
    "other": {
        "common_causes": [
            "Review experimental timeline and conditions",
            "Check all reagent expiration dates and storage conditions",
            "Verify cell line identity by STR profiling",
        ],
        "quick_checks": [
            "Repeat with fresh reagents",
            "Consult published protocols for your specific cell type",
            "Contact Cas9/guide RNA vendor technical support",
        ],
    },
}

PROMPT_PROCESS_TROUBLESHOOT_ADVISE = """Please act as an expert
CRISPR troubleshooting consultant. Given the diagnosis of the
problem, generate specific, actionable advice. Use the provided
domain knowledge to inform your recommendations. Please format
your response and make sure it is parsable by JSON.

Problem category: {category}
Problem summary: {summary}
Experimental details: {details}

Diagnosis:
{diagnosis}

Domain knowledge - Common causes for this category:
{common_causes}

Domain knowledge - Quick checks:
{quick_checks}

Generate a prioritized troubleshooting plan. Each action should be specific and actionable.

Response format:
{{
"Thoughts": "<analysis of the most likely issues and best approach>",
"Actions": [
    {{
        "priority": <1-based priority number>,
        "action": "<specific actionable step>",
        "rationale": "<why this addresses the likely cause>",
        "difficulty": "<easy|medium|hard>",
        "expected_impact": "<high|medium|low>"
    }}
],
"Summary": "<2-3 sentence summary of the recommended approach>"
}}"""
