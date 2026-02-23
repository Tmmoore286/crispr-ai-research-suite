"""Prompts for CRISPRa/CRISPRi transcriptional modulation workflows."""

PROMPT_REQUEST_ENTRY = """CRISPRa / CRISPRi planning

We will work through:
1. effector system selection
2. target and cellular context
3. guide-targeting strategy near TSS regions
"""

PROMPT_REQUEST_SYSTEM_SELECTION = """
Select a modulation system (or describe what effect size you need):
- Activation examples: dCas9-VP64, dCas9-VPR, dCas9-p65-HSF1, SunTag variants
- Repression examples: dCas9-KRAB, dCas9-KRAB-MeCP2
"""

PROMPT_PROCESS_SYSTEM_SELECTION = """Classify requested CRISPRa/CRISPRi system and mode.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Answer": "<system name>",
"Mode": "<activation|repression>"
}}"""

PROMPT_REQUEST_TARGET = """
Please provide:
1. target gene
2. species
3. relevant cell model
4. preferred modulation strength (if known)

Positioning reminder:
- activation guides commonly upstream of TSS
- repression guides commonly around TSS
"""

PROMPT_PROCESS_TARGET = """Extract CRISPRa/CRISPRi target metadata.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief analysis>",
"Target gene": "<symbol or NA>",
"Species": "<human|mouse|NA>",
"Cell type": "<cell type or NA>",
"Modulation level": "<strong|moderate|mild|NA>",
"TSS targeting note": "<placement notes>"
}}"""

PROMPT_REQUEST_GUIDE_DESIGN = """
Guide planning notes for transcriptional modulation:
- consider multiple guides per locus
- prioritize TSS-proximal regions based on mode
- avoid obviously problematic sequence features

Should I provide guide-design recommendations now?
"""

PROMPT_PROCESS_GUIDE_DESIGN = """Determine whether the user wants
CRISPRa/CRISPRi guide recommendations.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Choice": "<yes|no>"
}}"""
