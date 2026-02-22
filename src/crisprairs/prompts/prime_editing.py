"""Prime editing prompts for system selection and pegRNA design planning."""

PROMPT_REQUEST_ENTRY = """Prime editing setup

We will collect:
1. prime editor configuration
2. exact intended edit
3. pegRNA design starting parameters

Prime editing supports substitutions, short insertions, and short deletions without donor templates.
"""

PROMPT_REQUEST_SYSTEM_SELECTION = """
Select a prime editing configuration:
1. PE2
2. PE3
3. PE3b
4. PEmax

If you are unsure, describe your priority (efficiency vs purity) and I will suggest one.
"""

PROMPT_PROCESS_SYSTEM_SELECTION = """Identify the requested prime-editing configuration.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Answer": "<PE2|PE3|PE3b|PEmax>"
}}"""

PROMPT_REQUEST_TARGET = """
Describe the desired prime edit:
1. target gene
2. species
3. edit type (substitution/insertion/deletion/complex)
4. edit description in plain language
"""

PROMPT_PROCESS_TARGET = """Extract prime-editing target metadata.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief analysis>",
"Target gene": "<symbol or NA>",
"Species": "<human|mouse|NA>",
"Edit type": "<point_mutation|insertion|deletion|complex>",
"Edit description": "<requested edit>",
"Exon": "<exon or NA>",
"Sequence context": "<provided context or NA>"
}}"""

PROMPT_REQUEST_PEGRNA_DESIGN = """
pegRNA planning checkpoints:
- spacer near edit site
- PBS seed length to initialize testing
- RT template length to initialize testing

For PE3/PE3b workflows, a nicking guide is usually considered as a second lever.
Continue with pegRNA recommendation defaults?
"""

PROMPT_PROCESS_PEGRNA_DESIGN = """Decide if the user wants pegRNA recommendation defaults.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Choice": "<yes|no>",
"PBS_length": "<recommended PBS length; default 13>",
"RT_template_length": "<recommended RT template length; default 15>"
}}"""
