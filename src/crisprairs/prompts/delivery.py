"""Prompt templates for delivery method selection workflow."""

PROMPT_REQUEST_ENTRY = """
## Step: Delivery Method Selection

Choosing the right delivery method is critical for your CRISPR experiment's success. The delivery approach affects:
- **Editing efficiency** — some methods achieve higher transfection rates
- **Cell viability** — certain methods are gentler on sensitive cell types
- **Expression duration** — transient vs. stable expression impacts off-target risk
- **In vivo feasibility** — not all methods work for animal models

We'll help you select the optimal delivery method and format (plasmid, RNP, or mRNA) based on your experimental context.
"""

PROMPT_REQUEST_SELECT = """
To recommend the best delivery approach, please provide:
1. **Cell type** (e.g., HEK293T, primary T cells, iPSCs, mouse liver)
2. **In vivo or in vitro?**
3. **Any special constraints?** (e.g., low toxicity required, need stable integration, AAV size limit)

You can also just describe your experiment and we'll infer the best approach.
"""

PROMPT_PROCESS_SELECT = """Please act as an expert in CRISPR delivery methods. Given the user's experimental context, recommend the optimal delivery method and format. Think step by step.

Delivery Decision Matrix:
- Immortalized cell lines (HEK293T, HeLa, U2OS, A549, K562) -> Lipofection (Lipofectamine 3000) or electroporation; plasmid or RNP format
- Primary cells (T cells, HSPCs, iPSCs, neurons) -> Electroporation (Lonza 4D-Nucleofector) preferred; RNP format recommended for lower toxicity
- Hard-to-transfect cells -> Lentiviral or electroporation
- In vivo, liver -> LNP (lipid nanoparticle) with mRNA/RNP; AAV if persistent expression needed
- In vivo, brain/eye/muscle -> AAV (use SaCas9 if SpCas9 too large for AAV capacity ~4.7kb)
- In vivo, systemic -> LNP for liver tropism; AAV for tissue-specific promoters
- Therapeutic/clinical applications -> RNP format (transient, lower off-target, no integration risk)
- Large-scale screening -> Lentiviral (stable integration, selectable)

Format considerations:
- Plasmid: easiest, cheapest, but sustained expression increases off-target risk, possible random integration
- RNP (ribonucleoprotein): transient expression, lowest off-target, no DNA delivery, ideal for therapeutic use
- mRNA: transient, no integration risk, good for in vivo LNP delivery

User Input:
{user_message}

Response format:
{{
"Thoughts": "<step-by-step reasoning about the user's context>",
"delivery_method": "<lipofection|electroporation|lentiviral|AAV|LNP>",
"format": "<plasmid|RNP|mRNA>",
"reasoning": "<1-2 sentence explanation of why this combination is recommended>",
"specific_product": "<e.g., Lipofectamine 3000, Lonza 4D-Nucleofector, specific AAV serotype>",
"alternatives": "<backup option if primary doesn't work>"
}}"""
