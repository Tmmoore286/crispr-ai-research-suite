"""Prompt templates for Cas protein selection.

Cas system selection guidance based on published literature:
- Jinek et al., Science 2012 (SpCas9 mechanism)
- Cong et al., Science 2013 (SpCas9 genome editing in mammalian cells)
- Ran et al., Nature 2015 (SaCas9 for in vivo applications)
- Zetsche et al., Cell 2015 (Cpf1/Cas12a)
- Walton et al., Science 2020 (SpRY near-PAMless variant)
"""

PROMPT_REQUEST_CAS_SELECTION = """## Step: Cas Protein Selection

Choosing the right CRISPR nuclease is the foundation of your experiment. The choice depends on:
- **PAM availability** at your target site
- **Delivery constraints** (protein size, viral packaging)
- **Editing precision** requirements
- **Species and cell type**

**Available Cas Systems:**

| System | PAM | Size | Key Features |
|--------|-----|------|--------------|
| **SpCas9** | NGG | 4.1 kb | Gold standard, most validated, broadest tool ecosystem |
| **SaCas9** | NNGRRT | 3.2 kb | Compact — fits in AAV for in vivo delivery |
| **enCas12a** | TTTV | 3.9 kb | Staggered cuts, multiplex with single CRISPR array, no tracrRNA |
| **SpRYCas9** | NNN (relaxed) | 4.1 kb | Near-PAMless, access any target — lower specificity |

Please describe your experiment and we'll recommend the best Cas system, or select one directly.
"""

PROMPT_PROCESS_CAS_SELECTION = """Please act as an expert in
CRISPR nuclease selection. Given the user's experimental
context, recommend the optimal Cas system. Consider PAM
availability, delivery constraints, editing precision needs,
and target organism.

Selection guidelines (from published literature):
- Default to SpCas9 (NGG) for standard mammalian cell editing — most validated system
- Use SaCas9 (NNGRRT) when AAV packaging is needed (in vivo brain, eye, muscle)
- Use enCas12a (TTTV) for AT-rich targets, multiplex editing, or when staggered cuts preferred
- Use SpRYCas9 (NNN) only when no PAM is available for other systems — note reduced specificity
- For therapeutic applications, prefer high-fidelity variants (eSpCas9, HiFi Cas9)

{user_message}

Response format:
{{
"Thoughts": "<step-by-step reasoning about the user's needs>",
"Answer": "<SpCas9|SaCas9|enCas12a|SpRYCas9>",
"PAM": "<the PAM for the selected system>",
"Reasoning": "<1-2 sentence explanation>",
"Alternative": "<backup system if primary is unsuitable>"
}}"""
