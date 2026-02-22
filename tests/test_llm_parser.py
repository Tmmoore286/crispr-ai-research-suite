"""Tests for llm/parser.py — JSON extraction utilities."""

import pytest

from crisprairs.llm.parser import extract_json


class TestExtractJson:
    def test_plain_json(self):
        result = extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_whitespace(self):
        result = extract_json('  \n{"key": "value"}\n  ')
        assert result == {"key": "value"}

    def test_markdown_json_fence(self):
        text = '```json\n{"gene": "TP53"}\n```'
        result = extract_json(text)
        assert result == {"gene": "TP53"}

    def test_markdown_plain_fence(self):
        text = '```\n{"gene": "BRCA1"}\n```'
        result = extract_json(text)
        assert result == {"gene": "BRCA1"}

    def test_json_embedded_in_prose(self):
        text = 'Here is my analysis:\n{"result": "success", "gene": "TP53"}\nThat looks good.'
        result = extract_json(text)
        assert result["result"] == "success"

    def test_nested_json(self):
        text = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
        result = extract_json(text)
        assert result["outer"]["inner"] == "value"
        assert result["list"] == [1, 2, 3]

    def test_json_with_escaped_quotes(self):
        text = '{"message": "He said \\"hello\\"."}'
        result = extract_json(text)
        assert "hello" in result["message"]

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="Could not extract JSON"):
            extract_json("This is plain text with no JSON.")

    def test_markdown_fence_with_extra_text(self):
        text = """I think the best approach is:

```json
{"delivery_method": "electroporation", "format": "RNP"}
```

This is because RNP has lower off-target effects."""
        result = extract_json(text)
        assert result["delivery_method"] == "electroporation"
        assert result["format"] == "RNP"

    def test_multiple_json_objects_returns_first(self):
        text = '{"first": true} and {"second": true}'
        result = extract_json(text)
        assert result.get("first") is True
