"""Prompt templates for validation and primer design workflow."""

PROMPT_REQUEST_VALIDATION_ENTRY = """
## Step: Experiment Validation Strategy

After delivering your CRISPR components, you'll need to
validate that editing occurred. The validation approach depends
on your editing modality:

**Knockout (indel-based):**
- **T7 Endonuclease I (T7E1) assay** — Quick screening for indels (detects heteroduplexes)
- **Sanger sequencing** — Confirm indel spectrum, use with ICE or TIDE analysis
- **NGS (amplicon deep sequencing)** — Quantitative, resolves allele frequencies
- **Western blot** — Confirm protein loss

**Base Editing (C>T or A>G):**
- **Sanger sequencing + EditR/CRISPResso2** — Quantify base conversion efficiency
- **NGS** — Precise allele frequency and bystander editing analysis

**Prime Editing:**
- **NGS (deep sequencing)** — Required for precise edit verification
- **CRISPResso2** — Quantify correct edit vs. indels

**CRISPRa/CRISPRi:**
- **RT-qPCR** — Measure transcript-level expression changes
- **Western blot** — Confirm protein-level changes
- **Flow cytometry** — If targeting surface markers or fluorescent reporters

All validation methods require **PCR primers** flanking the
target site. We can design these for you.
"""

PROMPT_REQUEST_PRIMER_DESIGN = """
We've designed PCR validation primers flanking your CRISPR
target site. These primers will amplify a region suitable for
T7E1 assay, Sanger sequencing, or NGS analysis.

Review the primer pairs below and select the one you'd like to
use, or proceed with Pair 1 (recommended).
"""

PROMPT_REQUEST_BLAST = """
Would you like to verify your primers against the genome using NCBI BLAST? This checks for:
- **Primer specificity** — ensures primers bind uniquely to your target region
- **Off-target amplification** — identifies potential non-specific products

This step is optional but recommended. BLAST queries typically take 30-60 seconds.

Please respond **yes** or **no**.
"""

PROMPT_PROCESS_BLAST = """Please act as an expert in molecular
biology. Given the user input, determine if they want to run a
BLAST primer check. Please format your response and make sure
it is parsable by JSON.

User Input:
"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Choice": "<yes or no>"
}}"""
