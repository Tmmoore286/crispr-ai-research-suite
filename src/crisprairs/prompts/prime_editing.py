"""Prompt templates for prime editing workflow."""

PROMPT_REQUEST_ENTRY = """Now, let's start designing your prime editing experiment. We will go through a step-by-step process:

1. Selecting a prime editing system (PE2, PE3, PE3b, PEmax).
2. Defining the target edit (insertion, deletion, or base substitution).
3. Designing the pegRNA (spacer + PBS + RT template).

Prime editing enables precise edits without double-strand breaks or donor DNA:
- **All 12 types of point mutations** (any base to any base)
- **Small insertions** (up to ~44 bp efficiently)
- **Small deletions** (up to ~80 bp efficiently)
- **Combination edits** (substitution + insertion/deletion)
"""

PROMPT_REQUEST_SYSTEM_SELECTION = """
Please select the prime editing system you would like to use:

1. **PE2** — Prime editor 2 (nCas9-H840A fused to M-MLV RT)
   - The foundational PE system
   - Lower efficiency but fewer indels
   - Recommended for initial testing

2. **PE3** — PE2 + a nicking sgRNA on the non-edited strand
   - 1.5-5x higher efficiency than PE2
   - Slightly higher indel rate
   - Recommended for most applications

3. **PE3b** — PE3 with a nicking sgRNA that only matches after editing
   - Similar efficiency to PE3
   - Lower indel rate (nicking guide only binds after edit is installed)
   - Recommended when high purity is important

4. **PEmax** — Optimized PE2 with enhanced architecture
   - Codon-optimized RT, optimized NLS, improved linker
   - Highest efficiency PE system
   - Addgene #174820
"""

PROMPT_PROCESS_SYSTEM_SELECTION = """Please act as an expert in CRISPR prime editing technology. Given the user input, identify which prime editing system they want to use. Please format your response and make sure it is parsable by JSON.

Prime editing systems:
1. PE2 — Base prime editor (nCas9-RT fusion)
2. PE3 — PE2 + nicking sgRNA (higher efficiency)
3. PE3b — PE3 with edit-dependent nicking guide (fewer indels)
4. PEmax — Optimized PE2 architecture (highest efficiency)

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Answer": "<PE2|PE3|PE3b|PEmax>"
}}"""

PROMPT_REQUEST_TARGET = """
Please describe the edit you want to make:

1. What **gene** do you want to edit?
2. What **species** (human/mouse)?
3. What type of edit?
   - **Point mutation:** e.g., "Change C to T at position 248 of TP53"
   - **Small insertion:** e.g., "Insert FLAG tag after the start codon of MYC"
   - **Small deletion:** e.g., "Delete the 3bp causing deltaF508 in CFTR"
4. What is the **genomic context** around the edit site? (if known)

The more specific you are, the better we can design the pegRNA.
"""

PROMPT_PROCESS_TARGET = """Please act as an expert in CRISPR prime editing. Given the user input about their desired edit, extract the relevant information. Please format your response and make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<step-by-step analysis>",
"Target gene": "<gene symbol in uppercase, or NA>",
"Species": "<human|mouse|NA>",
"Edit type": "<point_mutation|insertion|deletion|complex>",
"Edit description": "<specific description of the desired edit>",
"Exon": "<target exon if specified, or NA>",
"Sequence context": "<any sequence context provided, or NA>"
}}"""

PROMPT_REQUEST_PEGRNA_DESIGN = """
Based on your target edit, here are the key design parameters for the pegRNA:

**pegRNA Components:**
1. **Spacer** (20 nt): Determines where Cas9 nicks the edited strand
   - Must have an NGG PAM near the edit site
   - Nick site should be close to the desired edit (ideally within 0-15 nt)

2. **Primer Binding Site (PBS)** (8-15 nt): Binds to the nicked strand
   - Typically 13 nt for SpCas9-based PE
   - Tm should be ~30C for optimal binding

3. **RT Template** (10-30+ nt): Encodes the desired edit + homology
   - Contains the edit sequence plus flanking homology
   - Longer templates = more precise but potentially lower efficiency

**Design Rules of Thumb:**
- Start with PBS = 13 nt, RT template = 10-15 nt beyond the edit
- Test 3-5 spacers near the edit site
- For PE3/PE3b: design a nicking guide 40-90 bp from the pegRNA nick site

Would you like us to provide pegRNA design recommendations? Please confirm.
"""

PROMPT_PROCESS_PEGRNA_DESIGN = """Please act as an expert in prime editing pegRNA design. Given the user confirmation, determine if we should proceed with pegRNA design guidance. Please format your response and make sure it is parsable by JSON.

User Input:

"{user_message}"

Response format:
{{
"Thoughts": "<thoughts>",
"Choice": "<yes|no>",
"PBS_length": "<recommended PBS length, default 13>",
"RT_template_length": "<recommended RT template length, default 15>"
}}"""
