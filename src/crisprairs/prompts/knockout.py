"""Prompt templates for the knockout workflow.

Guide RNA design for gene knockout uses runtime CRISPOR API scoring
rather than bundled sgRNA libraries. This enables knockout design
for any gene in any supported organism.

Scientific basis: CRISPR-Cas9 induces double-strand breaks repaired
by NHEJ, producing frameshift indels that disrupt the open reading frame.
Published guidelines: Doench et al., Nat Biotechnol 2014; Hsu et al., Cell 2013.
"""

PROMPT_REQUEST_TARGET_INPUT = """## Step: Knockout Target Selection

To design guide RNAs for gene knockout, please provide:

1. **Target gene** — gene symbol (e.g., TP53, BRCA1, CD274)
2. **Species** — human, mouse, rat, zebrafish, or drosophila
3. **Any preferences?** — specific exons, functional domains, or constraints

**Design strategy:**
- We target early constitutive exons to maximize frameshift probability
- Guides are scored for on-target efficiency and off-target specificity
- Multiple guides (3-5) are recommended for reliable knockout
"""

PROMPT_PROCESS_TARGET_INPUT = """Please act as an expert in
CRISPR gene knockout design. Given the user's input, extract
the target gene and species information.

{user_message}

Response format:
{{
"Thoughts": "<analysis of the user's knockout target>",
"Target gene": "<gene symbol in uppercase>",
"Species": "<human|mouse|rat|zebrafish|drosophila>",
"Preferred exon": "<exon number if specified, or 'early constitutive'>",
"Additional constraints": "<any user-specified constraints>"
}}"""

PROMPT_REQUEST_GUIDE_REVIEW = """## Guide RNA Candidates

We've identified guide RNA candidates for your knockout target
using CRISPOR scoring. The guides are ranked by specificity
score (MIT algorithm).

**Scoring criteria:**
- **MIT Specificity Score** (0-100): Higher = fewer predicted off-targets. Aim for >80.
- **Doench 2016 Score** (0-100): Predicts on-target cutting efficiency. Aim for >50.
- **Off-target count**: Number of predicted off-target sites in the genome.

Please review the candidates and select guides to proceed with, or we'll use the top-ranked guides.
"""

PROMPT_PROCESS_GUIDE_SELECTION = """Please act as an expert in
CRISPR guide RNA selection. Given the user's input about guide
selection, determine which guides they want to proceed with.

{user_message}

Response format:
{{
"Thoughts": "<analysis of the user's guide preferences>",
"Selection": "<all|top3|specific indices or 'as recommended'>",
"Proceed": "<yes|no>"
}}"""
