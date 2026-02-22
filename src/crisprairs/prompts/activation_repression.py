"""Prompt templates for CRISPRa/CRISPRi (activation/repression) workflow."""

PROMPT_REQUEST_ENTRY = """Now, let's design your CRISPRa or CRISPRi experiment for transcriptional modulation. We will go through a step-by-step process:

1. Selecting an activation or repression system.
2. Defining the target gene and regulatory region.
3. Designing guide RNA targeting the promoter/TSS region.

**CRISPRa (Activation):** Uses catalytically dead Cas9 (dCas9) fused to transcriptional activators to upregulate gene expression.
**CRISPRi (Interference/Repression):** Uses dCas9 fused to transcriptional repressors to downregulate gene expression.
"""

PROMPT_REQUEST_SYSTEM_SELECTION = """
Please select the CRISPRa/CRISPRi system you would like to use:

**CRISPRa (Activation) Systems:**
1. **dCas9-VP64** — Simple activation, moderate (2-10x) upregulation
2. **dCas9-p65-HSF1 (SPH)** — Synergistic activation, strong (10-100x) upregulation
3. **dCas9-VPR** — VP64-p65-Rta fusion, very strong activation
4. **SunTag-VP64** — Array-based recruitment, strong and tunable activation

**CRISPRi (Repression) Systems:**
5. **dCas9-KRAB** — Standard repression, 50-90% knockdown
6. **dCas9-KRAB-MeCP2** — Enhanced repression with additional silencing domain

Or describe your needs and we can recommend a system.
"""

PROMPT_PROCESS_SYSTEM_SELECTION = """Please act as an expert in CRISPRa/CRISPRi technology. Given the user input, identify which system they want to use. Please format your response and make sure it is parsable by JSON.

CRISPRa systems: dCas9-VP64, dCas9-p65-HSF1, dCas9-VPR, SunTag-VP64
CRISPRi systems: dCas9-KRAB, dCas9-KRAB-MeCP2

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Answer": "<system name>",
"Mode": "<activation|repression>"
}}"""

PROMPT_REQUEST_TARGET = """
Please describe your target:

1. What **gene** do you want to activate or repress?
2. What **species** (human/mouse)?
3. What **cell type** are you working with? (important for promoter activity)
4. What **level of modulation** do you need? (e.g., "strong activation", "moderate repression")

**Important note on guide design for CRISPRa/CRISPRi:**
- For **CRISPRa**: guides should target **upstream** of the TSS (typically -400 to -50 bp)
- For **CRISPRi**: guides should target **around the TSS** (typically +50 to -50 bp relative to TSS)
- Guides on the **non-template strand** generally work better for CRISPRi
"""

PROMPT_PROCESS_TARGET = """Please act as an expert in CRISPRa/CRISPRi. Given the user input about their target, extract the relevant information. Please format your response and make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<step-by-step analysis>",
"Target gene": "<gene symbol in uppercase, or NA>",
"Species": "<human|mouse|NA>",
"Cell type": "<cell type if specified, or NA>",
"Modulation level": "<strong|moderate|mild, or NA>",
"TSS targeting note": "<any notes about TSS targeting region>"
}}"""

PROMPT_REQUEST_GUIDE_DESIGN = """
For effective CRISPRa/CRISPRi guide design, consider:

**Guide Placement:**
- CRISPRa guides: -400 to -50 bp relative to TSS (transcription start site)
- CRISPRi guides: +50 to -50 bp relative to TSS
- Multiple guides (3-5) are recommended for reliable modulation

**Design Tips:**
- Use 2-5 guides per gene for robust effects
- Avoid guides overlapping with transcription factor binding sites (for CRISPRa)
- Non-template strand guides preferred for CRISPRi
- Standard sgRNA design rules apply (avoid poly-T, off-target minimization)

**Recommended tools:**
- CRISPick (Broad Institute): guides scored for CRISPRa/CRISPRi
- CHOPCHOP: includes CRISPRa/CRISPRi mode

Would you like us to provide guide design recommendations?
"""

PROMPT_PROCESS_GUIDE_DESIGN = """Please act as an expert in CRISPRa/CRISPRi guide design. Given the user's response, determine if we should proceed with design recommendations. Please format your response and make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Choice": "<yes|no>"
}}"""
