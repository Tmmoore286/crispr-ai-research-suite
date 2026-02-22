"""Delivery selection prompts for choosing transfer method and payload format."""

PROMPT_REQUEST_ENTRY = """
## Delivery Planning

Delivery strategy usually determines whether a design succeeds in practice.
Key tradeoffs:
- transfection/transduction efficiency
- viability impact and stress response
- persistence of editor exposure (transient vs sustained)
- fit for in vivo constraints

I will suggest a method and payload format using your context.
"""

PROMPT_REQUEST_SELECT = """
Please share:
1. Cell or tissue context (for example: HEK293T, primary T cells, iPSC-derived neurons, mouse liver)
2. In vitro vs in vivo
3. Any hard constraints (toxicity ceiling, stable integration requirement, AAV size limit, throughput)

Free-form descriptions are fine.
"""

PROMPT_PROCESS_SELECT = """You are advising CRISPR delivery planning for research use.
Infer the best method and payload format from the user context.

Heuristics:
- Immortalized lines: lipofection or electroporation; plasmid or RNP.
- Primary/sensitive cells: electroporation with RNP favored.
- Hard-to-transfect or pooled screening: lentiviral workflows are often practical.
- In vivo liver: LNP with mRNA/RNP is often first choice.
- In vivo eye/brain/muscle: AAV frequently used; compact nucleases may be needed.
- Clinical-leaning workflows: favor transient exposure (often RNP).

Payload guidance:
- plasmid: operationally simple, prolonged expression.
- RNP: transient, low integration risk.
- mRNA: transient, useful with LNP.

User message:
{user_message}

Return JSON only:
{{
"Thoughts": "<brief reasoning>",
"delivery_method": "<lipofection|electroporation|lentiviral|AAV|LNP>",
"format": "<plasmid|RNP|mRNA>",
"reasoning": "<short recommendation rationale>",
"specific_product": "<recommended product/platform>",
"alternatives": "<backup option>"
}}"""
