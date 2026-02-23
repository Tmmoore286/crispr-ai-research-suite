"""Base editing workflow prompts (CBE/ABE and guide placement constraints)."""

PROMPT_REQUEST_ENTRY = """Base editing setup

We will walk through:
1. editor family selection
2. target/base-change capture
3. guide strategy checks for editor window compatibility

Reminder:
- CBE typically supports C>T conversions
- ABE typically supports A>G conversions
"""

PROMPT_REQUEST_SYSTEM_SELECTION = """
Choose a base editor family:
1. CBE
2. ABE
3. Dual editor

If unsure, describe your desired mutation and I will infer a recommendation.
"""

PROMPT_PROCESS_SYSTEM_SELECTION = """Classify the user's requested base editor.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Answer": "<CBE|ABE|Dual>"
}}"""

PROMPT_REQUEST_TARGET = """
Describe the intended edit:
1. gene
2. species
3. base change (for example, C>T or A>G)
4. optional codon/protein position details
"""

PROMPT_PROCESS_TARGET = """Extract structured base-editing target details.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief analysis>",
"Target gene": "<symbol or NA>",
"Species": "<human|mouse|NA>",
"Base change": "<change string>",
"Specific position": "<position or NA>",
"Exon": "<exon or NA>",
"Editing window note": "<window constraints or NA>"
}}"""

PROMPT_REQUEST_GUIDE_DESIGN = """
Guide constraints for base editing:
- CBE windows are often centered around protospacer positions 4-8
- ABE windows are often centered around positions 4-7
- Avoid unintended bystander edits inside the active window

Would you like guide-design recommendations now?
"""

PROMPT_PROCESS_GUIDE_DESIGN = """Determine whether the user wants to continue
with base-editing guide design.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Choice": "<yes|no>",
"Additional_constraints": "<extra constraints if any>"
}}"""
