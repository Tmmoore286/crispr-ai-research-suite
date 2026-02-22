"""Validation and primer-check prompts."""

PROMPT_REQUEST_VALIDATION_ENTRY = """
## Validation Planning

Choose validation depth according to modality and assay goals.
Common options include mismatch assays, Sanger/NGS readouts, and expression-level checks.
Primer design is required for most locus-level confirmation workflows.
"""

PROMPT_REQUEST_PRIMER_DESIGN = """
Primer candidates have been generated around the target locus.
Review the pairs and select one, or continue with the first pair as default.
"""

PROMPT_REQUEST_BLAST = """
Would you like an optional BLAST specificity check for the selected primers?
Reply yes or no.
"""

PROMPT_PROCESS_BLAST = """Interpret whether the user requested primer BLAST verification.

User input:
"{user_message}"

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"Choice": "<yes|no>"
}}"""
