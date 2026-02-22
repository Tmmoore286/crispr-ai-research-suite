"""JSON extraction and parsing utilities for LLM responses."""

from __future__ import annotations

import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Extract a JSON object from LLM response text.

    Handles common LLM output patterns:
    - Plain JSON
    - JSON wrapped in markdown code fences (```json ... ```)
    - JSON embedded in surrounding prose

    Args:
        text: Raw text from the LLM.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If no valid JSON object can be extracted.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    stripped = _strip_code_fences(text)
    if stripped != text:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Find JSON object in the text using brace matching
    result = _find_json_object(text)
    if result is not None:
        return result

    raise ValueError(f"Could not extract JSON from LLM response: {text[:200]}...")


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from text."""
    # Match ```json ... ``` or ``` ... ```
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _find_json_object(text: str) -> dict | None:
    """Find the first valid JSON object in text using brace matching."""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(text)):
        c = text[i]

        if escape_next:
            escape_next = False
            continue

        if c == "\\":
            escape_next = True
            continue

        if c == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Try next opening brace
                    next_start = text.find("{", start + 1)
                    if next_start != -1:
                        return _find_json_object(text[next_start:])
                    return None

    return None
