"""Prompt templates for base editing workflow."""

PROMPT_REQUEST_ENTRY = """Now, let's start designing your base
editing experiment. We will go through a step-by-step process:

1. Selecting a base editing system (CBE or ABE).
2. Defining the target base change and editing window.
3. Designing guide RNA with editing window constraints.

Base editing enables precise single-nucleotide conversions without double-strand breaks:
- **CBE (Cytosine Base Editor):** Converts C-to-T (or G-to-A on opposite strand)
- **ABE (Adenine Base Editor):** Converts A-to-G (or T-to-C on opposite strand)
"""

PROMPT_REQUEST_SYSTEM_SELECTION = """
Please select the base editing system you would like to use,
or describe your needs and we can recommend one.

1. **CBE (Cytosine Base Editor)** — BE4max, BE4-GAM, or similar
   - Converts C-to-T within editing window (positions 4-8 of protospacer)
   - Applications: Creating stop codons, disrupting splice sites, correcting T>C pathogenic variants
   - Recommended: Addgene #112093 (BE4max) for highest efficiency

2. **ABE (Adenine Base Editor)** — ABE8e, ABE7.10, or similar
   - Converts A-to-G within editing window (positions 4-7 of protospacer)
   - Applications: Correcting G>A pathogenic variants, modifying regulatory elements
   - Recommended: Addgene #138489 (ABE8e) for highest efficiency

3. **Dual Base Editor** — SPACE, TARGET-AID, or similar
   - Can perform both C-to-T and A-to-G conversions
   - More experimental, lower efficiency
"""

PROMPT_PROCESS_SYSTEM_SELECTION = """Please act as an expert in
CRISPR base editing technology. Given the user input, identify
which base editing system they want to use. Please format your
response and make sure it is parsable by JSON.

Base editing systems:
1. CBE — Cytosine Base Editor (C-to-T conversion, e.g., BE4max, BE4-GAM)
2. ABE — Adenine Base Editor (A-to-G conversion, e.g., ABE8e, ABE7.10)
3. Dual — Dual base editor (both conversions)

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Answer": "<CBE|ABE|Dual>"
}}"""

PROMPT_REQUEST_TARGET = """
Please describe your target base change:

1. What **gene** do you want to edit?
2. What **species** (human/mouse)?
3. What specific **base change** do you want to make?
   (e.g., "C>T at position 248 of TP53", or
   "correct the A>G variant in BRCA1 exon 10")
4. Do you have a specific **codon or amino acid change** in mind?

If you're not sure about the exact position, just describe the
gene and the type of change you need, and we'll help identify
suitable target sites.
"""

PROMPT_PROCESS_TARGET = """Please act as an expert in CRISPR base
editing. Given the user input about their desired base edit,
extract the relevant information. Please format your response
and make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<step-by-step analysis>",
"Target gene": "<gene symbol in uppercase, or NA>",
"Species": "<human|mouse|NA>",
"Base change": "<C>T or A>G or other>",
"Specific position": "<amino acid/codon position if specified, or NA>",
"Exon": "<target exon if specified, or NA>",
"Editing window note": "<any constraints on the editing window placement>"
}}"""

PROMPT_REQUEST_GUIDE_DESIGN = """
Based on your target, here are the key constraints for guide RNA design in base editing:

**Editing Window Rules:**
- CBE (BE4max): Target C must be at positions **4-8** of the
  protospacer (counting from 5' end, PAM-distal)
- ABE (ABE8e): Target A must be at positions **4-7** of the protospacer
- The PAM (NGG for SpCas9-based editors) must be properly
  positioned relative to the target base

**Design Considerations:**
- Avoid bystander edits (other C's or A's within the editing window)
- Check for target base accessibility in the editing window
- Consider using high-fidelity Cas9 variants to reduce off-target editing

Would you like us to search for suitable guides? Please confirm
the gene and species, or provide additional targeting constraints.
"""

PROMPT_PROCESS_GUIDE_DESIGN = """Please act as an expert in
CRISPR base editing guide RNA design. Given the user
confirmation and the context of base editing, determine if we
should proceed with guide search. Please format your response
and make sure it is parsable by JSON.

User Input:

"{user_message}"

Context: The user is designing guide RNAs for base editing.
They need guides where the target base falls within the editing
window (positions 4-8 for CBE, 4-7 for ABE).

Response format:
{{
"Thoughts": "<thoughts>",
"Choice": "<yes|no>",
"Additional_constraints": "<any additional constraints the user mentioned>"
}}"""
