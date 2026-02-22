"""Shared prompt utilities and formatting helpers."""

from __future__ import annotations


def json_response_instruction(schema_description: str) -> str:
    """Generate a standard JSON response instruction block for LLM prompts.

    Args:
        schema_description: The JSON schema example with placeholders.

    Returns:
        Formatted instruction string to append to prompts.
    """
    return (
        "Please format your response as valid JSON. "
        "Do not include any text outside the JSON object.\n\n"
        f"Response format:\n{schema_description}"
    )


def format_user_input_block(user_message: str) -> str:
    """Format user input for embedding in an LLM prompt."""
    return f'User Input:\n\n"{user_message}"'


# Standard system preamble for CRISPR expert prompts
CRISPR_EXPERT_PREAMBLE = (
    "You are an expert in CRISPR genome editing technology, "
    "with deep knowledge of guide RNA design, delivery methods, "
    "and experimental validation. Think step by step."
)
