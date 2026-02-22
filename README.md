# CRISPR AI Research Suite

**AI-guided CRISPR experiment design — from target gene to bench-ready protocol.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Tmmoore286/crispr-ai-research-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/Tmmoore286/crispr-ai-research-suite/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Tmmoore286/crispr-ai-research-suite)](https://github.com/Tmmoore286/crispr-ai-research-suite/stargazers)

## What It Does

CRISPR AI Research Suite is a conversational AI platform that walks researchers through the full CRISPR experiment design workflow. You describe your experiment — the tool handles guide RNA design, delivery optimization, primer validation, and protocol generation.

The platform covers eight workflows end-to-end: gene knockout, base editing (CBE/ABE), prime editing (PE2/PE3/PEmax), CRISPRa activation, CRISPRi repression, off-target analysis, validation with primer design, and troubleshooting failed experiments. Each workflow produces bench-ready Markdown protocols with reagent catalog numbers (Addgene plasmid IDs, IDT protein catalog numbers, NEB enzyme references), ready to print and bring to the hood.

All guide RNA design happens at runtime via the CRISPOR API — no bundled sgRNA libraries, no stale genome builds. The tool queries Ensembl for genomic sequences, CRISPOR for guide scoring, NCBI for gene annotations, Primer3 for validation primer design, and BLAST for primer specificity checks.

## Why Use This

- **Designs guides at runtime via CRISPOR** — always uses current genome builds (hg38, mm10, rn6, danRer11, dm6, ce11), works for any gene in 6 model organisms, no bundled sgRNA libraries
- **Bench-ready protocols** — Markdown output with step-by-step instructions, reagent catalog numbers (Addgene, IDT, Thermo Fisher, NEB, Sigma), controls, and expected results
- **Built-in biosafety screening** — automatic germline editing flags (NIH Guidelines Section III-C), Federal Select Agent Program pathogen checks (42 CFR 73), and dual-use research of concern (DURC) review per USG policy
- **Sequence privacy** — detects identifiable genomic sequences (>50 bases) before they reach LLM providers, per NIH GDS Policy (NOT-OD-14-124)
- **Session management** — save, resume, and export experiments as Markdown or JSON; append-only JSONL audit trail for every LLM call and workflow event
- **Collaboration** — share sessions via token, add step-level annotations, request and complete PI review workflows (approve/revise/reject)
- **Experiment tracking** — log wet-lab results (editing efficiency, off-target detection, phenotype confirmation) linked to sessions; compare results across experiments
- **No vendor lock-in** — works with OpenAI (GPT-4o default) or Anthropic (Claude Sonnet default); switch providers with one env var, override models with another

## Example Conversation

Here is what a typical knockout workflow looks like in the chat interface:

> **Assistant:** Welcome to CRISPR AI Research Suite. Choose a workflow:
> 1. Knockout  2. Base Editing  3. Prime Editing  4. Activation  5. Repression  6. Off-Target Analysis  7. Troubleshoot
>
> **You:** 1
>
> **Assistant:** To design guide RNAs for gene knockout, please provide:
> 1. **Target gene** — gene symbol (e.g., TP53, BRCA1, CD274)
> 2. **Species** — human, mouse, rat, zebrafish, or drosophila
> 3. **Any preferences?** — specific exons, functional domains, or constraints
>
> Design strategy: We target early constitutive exons to maximize frameshift probability. Multiple guides (3-5) are recommended for reliable knockout.
>
> **You:** TP53 in human HEK293T cells
>
> **Assistant:** **Target gene:** TP53 | **Species:** human | **Cas system:** SpCas9 | **Strategy:** Target early constitutive exons
>
> **Guide RNA Candidates** (via CRISPOR, MIT scoring):
>
> | # | Sequence | MIT Score | Off-targets |
> |---|----------|-----------|-------------|
> | 1 | `CCATTGTTCAATATCGTCCG` | 92.4 | 2 |
> | 2 | `GACGGAAACCGTAGCTGCCC` | 87.1 | 5 |
> | 3 | `TCAACAAGATGTTTTGCCAA` | 83.6 | 8 |
>
> Scoring: **MIT Specificity Score** (0-100, higher = fewer off-targets, aim for >80). **Doench 2016** (0-100, predicts on-target efficiency, aim for >50).
>
> **You:** Use the top 3
>
> **Assistant:** Selected 3 guides for knockout of **TP53**. Now let's choose a delivery method...
>
> *(workflow continues through delivery selection, primer design, BLAST check, and protocol export)*

### Example Protocol Output

The exported protocol includes reagent catalog numbers and step-by-step instructions:

```markdown
# CRISPR Experiment Protocol

**Date Generated:** 2026-02-22
**Session ID:** a1b2c3d4e5f6
**Target Gene:** TP53
**Species:** human
**CRISPR System:** SpCas9
**Modality:** Knockout
**Delivery Method:** lipofection
**Delivery Format:** RNP

## Materials

### CRISPR Components
- **Plasmid:** Addgene #42230 (pX330-U6-Chimeric_BB-CBh-hSpCas9)
- **Protein:** IDT Alt-R S.p. Cas9 Nuclease V3 (Cat# 1081058)
- **tracrRNA:** IDT Alt-R CRISPR-Cas9 tracrRNA (Cat# 1072532)

### General Reagents
- **Transfection:** Lipofectamine 3000 (Thermo Fisher Cat# L3000001)
- **Culture Medium:** DMEM + 10% FBS + 1% Pen/Strep
- **Puromycin:** Puromycin dihydrochloride (Sigma Cat# P8833)
- **T7E1:** T7 Endonuclease I (NEB Cat# M0302S)

## sgRNA Sequences

| # | Sequence             | Score | Source  |
|---|----------------------|-------|---------|
| 1 | CCATTGTTCAATATCGTCCG | 92.4  | crispor |
| 2 | GACGGAAACCGTAGCTGCCC | 87.1  | crispor |
| 3 | TCAACAAGATGTTTTGCCAA | 83.6  | crispor |

## Experimental Steps

### 1. Construct Preparation
- Clone sgRNA oligos into the SpCas9 expression vector
- Verify insert by Sanger sequencing

### 2. Cell Culture
- Maintain target cells in recommended culture medium
- Passage cells to 70-80% confluency before transfection

### 3. Delivery
- Transfect cells using Lipofectamine 3000 following manufacturer's protocol
- Pre-complex Cas9 protein with sgRNA (1:1.2 molar ratio) for 10 min at RT
- Mix RNP complex with Lipofectamine 3000 reagent
- Include untransfected control wells

### 4. Selection (if applicable)
- Add puromycin (1-3 ug/mL) 24h post-transfection
- Maintain selection for 48-72h

### 5. Validation
- Extract genomic DNA 48-72h post-transfection
- PCR amplify the TP53 target region
- Perform T7 Endonuclease I (T7E1) assay or Sanger sequencing
- Optionally confirm by Western blot for TP53 protein loss

## Controls
- **Negative control:** Non-targeting sgRNA (scrambled sequence)
- **Untransfected control:** Cells without any construct
- **Positive control:** Previously validated sgRNA (if available)

## Expected Results
- T7E1 assay should show cleavage bands indicating indel formation
- Expected editing efficiency: 20-80% depending on guide and cell type
- Western blot should show reduced or absent protein expression
```

## Supported Workflows

### Knockout

Gene disruption via NHEJ-induced frameshift indels. The workflow fetches genomic sequence from Ensembl, submits it to the CRISPOR API for guide design, and returns guides ranked by MIT specificity score (off-target prediction) and Doench 2016 score (on-target efficiency). Targets early constitutive exons by default to maximize frameshift probability. Continues through delivery selection, primer design with BLAST verification, and protocol export with T7E1 validation steps.

**Pipeline:** Target Input → Guide Design (CRISPOR) → Guide Selection → Delivery → Validation → Primer Design → BLAST Check → Protocol Export

### Base Editing

Single-base conversions without double-strand breaks. Supports CBE (cytosine base editors, C-to-T conversion, editing window positions 4-8) and ABE (adenine base editors, A-to-G conversion, editing window positions 4-7). The workflow validates that the requested base change matches the selected editor type (warns if you select CBE but request an A>G change), explains editing window constraints, and recommends external tools like BE-Designer and BE-Hive for guide placement.

**Pipeline:** Entry → System Select (CBE/ABE) → Target Input → Guide Design → Delivery → Validation → Primer Design → BLAST Check

### Prime Editing

Precise insertions, deletions, and all 12 types of point mutations without DSBs or donor DNA. Supports PE2 (base system), PE3 (with nicking guide for 1.5-5x higher efficiency), PE3b (edit-dependent nicking for fewer indels), and PEmax (optimized architecture, highest efficiency). Explains pegRNA components: spacer (20 nt), primer binding site (8-15 nt), and RT template (10-30+ nt). For PE3/PE3b, notes that the nicking guide should be placed 40-90 bp from the edit site.

**Pipeline:** Entry → System Select (PE2/PE3/PE3b/PEmax) → Target Input → pegRNA Design → Delivery → Validation → Primer Design → BLAST Check

### CRISPRa / CRISPRi

Transcriptional modulation using catalytically dead Cas9 (dCas9) fused to effector domains.

- **CRISPRa (activation):** dCas9-VP64, dCas9-SPH, dCas9-VPR, SunTag-VP64. Guides target -400 to -50 bp upstream of the TSS. Expect 2-100x activation depending on system and gene.
- **CRISPRi (repression):** dCas9-KRAB, dCas9-KRAB-MeCP2. Guides target +50 to -50 bp around the TSS. Expect 50-95% repression depending on guide position.

Validation via RT-qPCR normalized to housekeeping genes (GAPDH or ACTB).

**Pipeline:** Entry → System Select → Target Input → Guide Design → Delivery

### Off-Target Analysis

Standalone guide specificity assessment. Submit existing 20 bp guide sequences, and the tool scores them via the CRISPOR API, then uses the LLM to generate a structured risk assessment. Risk levels: low (MIT >80, <10 off-targets), medium (50-80 or 10-100), high (<50 or >100). Optionally provides CRISPRitz installation and usage instructions for deep genome-wide analysis that accounts for DNA/RNA bulges.

**Pipeline:** Entry → Guide Input → CRISPOR Scoring → Risk Report

### Delivery Optimization

Cell-type-aware delivery method selection based on a published decision matrix:

| Scenario | Recommended Method | Format |
|----------|-------------------|--------|
| Immortalized cell lines (HEK293T) | Lipofection (Lipofectamine 3000) or electroporation | Plasmid or RNP |
| Primary cells (T cells, iPSCs) | Electroporation (Lonza 4D-Nucleofector) | RNP preferred |
| Hard-to-transfect cells | Lentiviral or electroporation | Stable or RNP |
| In vivo liver | LNP | mRNA or RNP |
| In vivo brain/eye/muscle | AAV (with compact SaCas9) | AAV vector |
| Therapeutic/clinical | RNP format | Transient, low off-target |
| Large-scale screening | Lentiviral (lentiCRISPR v2) | Stable integration |

Returns specific product recommendations, reagent details, reasoning, and alternative methods.

### Validation & Primer Design

Automated PCR primer design for editing verification. Uses Primer3 (optimal Tm 60 C, product size 200-500 bp, 3 pairs returned) with flanking sequence from Ensembl (500 bp expansion). Optional NCBI BLAST specificity check to verify primers bind only the intended target (submits each primer separately, checks hit counts). Validation strategies are modality-specific:

- **Knockout:** T7E1 assay, Sanger sequencing, optional NGS and Western blot
- **Base editing:** Sanger + EditR/CRISPResso2 quantification, optional NGS
- **Prime editing:** Deep sequencing required, CRISPResso2 quantification
- **CRISPRa/CRISPRi:** RT-qPCR, optional Western blot and flow cytometry

### Troubleshooting

Diagnoses failed CRISPR experiments through systematic root-cause analysis. Categorizes the issue (low efficiency, high toxicity, off-target effects, unexpected phenotype, or other), collects experimental details (cell type, delivery, system, guides, timepoint), generates a differential diagnosis with probability ratings, then produces a prioritized troubleshooting plan.

Built-in domain knowledge includes common causes and quick checks for each category. For example, low efficiency troubleshooting covers guide design quality, delivery optimization, Cas9 expression levels, chromatin accessibility, PAM availability, RNP degradation, and cell-line resistance — with quick checks like transfection efficiency reporters, positive control guides, and Western blot for Cas9 expression.

## Supported Organisms

| Common Name | Genome Build | Ensembl Species | NCBI TaxID |
|------------|-------------|-----------------|------------|
| Human | hg38 | *Homo sapiens* | 9606 |
| Mouse | mm10 | *Mus musculus* | 10090 |
| Rat | rn6 | *Rattus norvegicus* | 10116 |
| Zebrafish | danRer11 | *Danio rerio* | 7955 |
| Drosophila | dm6 | *Drosophila melanogaster* | 7227 |
| C. elegans | ce11 | *Caenorhabditis elegans* | 6239 |

## Quick Start

**Prerequisites:** Python 3.10+ and pip.

```bash
# Clone
git clone https://github.com/Tmmoore286/crispr-ai-research-suite.git
cd crispr-ai-research-suite

# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your API keys (see Configuration below)

# Run
python -m crisprairs.app
```

The app launches at `http://localhost:7860` with three tabs:

- **Chat** — conversational workflow interface with send/new session buttons and thumbs up/down feedback
- **Protocol Export** — generates a structured Markdown protocol from the current session
- **Session Export** — exports the full conversation and session data as Markdown

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `openai` or `anthropic` |
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Your Anthropic API key |
| `OPENAI_MODEL` | Optional | Override OpenAI model (default: `gpt-4o`). Also supports `OPENAI_MODEL_TURBO` for turbo-tier calls. |
| `ANTHROPIC_MODEL` | Optional | Override Anthropic model (default: `claude-sonnet-4-6-20250514`). Also supports `ANTHROPIC_MODEL_TURBO`. |
| `NCBI_EMAIL` | Recommended | Email for NCBI Entrez API (required by NCBI usage policy) |
| `NCBI_API_KEY` | Optional | NCBI API key for higher rate limits |

## How It Works

The platform uses a pipeline execution engine built around a `WorkflowStep` abstract base class. Each workflow is a sequence of steps registered with a `Router`. A `PipelineRunner` advances through steps, handling four result types:

- **CONTINUE** — auto-advance to the next step (no user interaction needed)
- **WAIT_FOR_INPUT** — pause and display a prompt; resume when the user responds
- **DONE** — step sequence complete
- **BRANCH** — switch to a different workflow modality mid-pipeline

All session state lives in a typed `SessionContext` dataclass with fields for target gene, species, modality, Cas system, guides (scored GuideRNA objects), delivery info, primer pairs, off-target results, troubleshooting data, and chat history. No untyped dictionaries — everything is explicit.

A typical knockout workflow progresses through 9 steps:

1. `KnockoutTargetInput` — collect gene and species from user, parse via LLM
2. `KnockoutGuideDesign` — fetch sequence from Ensembl, design guides via CRISPOR API
3. `KnockoutGuideSelection` — display scored guide table, let user choose
4. `DeliveryEntry` — show experiment context and delivery considerations
5. `DeliverySelect` — collect cell type/constraints, recommend delivery method via LLM
6. `ValidationEntry` — explain modality-specific validation strategies
7. `PrimerDesignStep` — design PCR primers via Primer3 with Ensembl flanking sequence
8. `BlastCheckStep` — optional NCBI BLAST primer specificity verification
9. `AutomationStep` — generate structured protocol from templates (no eval/exec)

Every LLM call passes through privacy screening (rejects requests with >50 base sequences) and is logged to an append-only audit trail with provider, model, and latency.

## Architecture

```
src/crisprairs/
├── app.py                  # Gradio UI (3 tabs: Chat, Protocol Export, Session Export)
├── __main__.py             # Entry point for python -m crisprairs.app
├── engine/                 # Pipeline execution engine
│   ├── workflow.py          # WorkflowStep ABC, StepResult enum, StepOutput, Router
│   ├── context.py           # SessionContext, GuideRNA, DeliveryInfo, PrimerPair dataclasses
│   └── runner.py            # PipelineRunner (step sequencing, input collection, branching)
├── llm/                    # LLM provider abstraction (no langchain)
│   ├── provider.py          # OpenAIChat, AnthropicChat, ChatProvider router + audit logging
│   └── parser.py            # JSON extraction from LLM responses, markdown fence stripping
├── safety/                 # Biosafety and privacy checks
│   ├── biosafety.py         # Germline keywords, Select Agent list, DURC patterns → BiosafetyFlag
│   └── privacy.py           # Identifiable genomic sequence detection (>50 bases)
├── workflows/              # CRISPR experiment workflow steps (30+ WorkflowStep subclasses)
│   ├── knockout.py          # KnockoutTargetInput, KnockoutGuideDesign, KnockoutGuideSelection
│   ├── base_editing.py      # BaseEditingEntry, SystemSelect, Target, GuideDesign
│   ├── prime_editing.py     # PrimeEditingEntry, SystemSelect, Target, GuideDesign
│   ├── activation_repression.py  # ActRepEntry, SystemSelect, Target, GuideDesign
│   ├── off_target.py        # OffTargetEntry, Input, Scoring, Report
│   ├── delivery.py          # DeliveryEntry, DeliverySelect (shared across workflows)
│   ├── validation.py        # ValidationEntry, PrimerDesignStep, BlastCheckStep (shared)
│   ├── troubleshoot.py      # TroubleshootEntry, Diagnose, Advise + TROUBLESHOOT_KNOWLEDGE
│   └── automation.py        # AutomationStep + protocol templates (cell culture, transfection, T7E1, Sanger)
├── prompts/                # LLM prompt templates (one file per workflow)
│   ├── common.py            # Shared utilities: JSON response instructions, CRISPR expert preamble
│   ├── knockout.py          # Target input, guide review, guide selection prompts
│   ├── base_editing.py      # CBE/ABE system selection, editing window, guide design prompts
│   ├── prime_editing.py     # PE system selection, pegRNA design, PBS/RT template prompts
│   ├── activation_repression.py  # Effector system selection, TSS targeting prompts
│   ├── off_target.py        # Guide input, risk assessment, CRISPRitz guidance prompts
│   ├── delivery.py          # Cell type collection, decision matrix, product recommendation prompts
│   ├── validation.py        # Strategy explanation, primer selection, BLAST check prompts
│   ├── troubleshoot.py      # Issue categorization, differential diagnosis, troubleshooting plan prompts
│   └── cas_selection.py     # Cas protein selection guidance (SpCas9, SaCas9, Cas12a, SpRY)
├── apis/                   # External API clients (all with explicit timeouts, graceful degradation)
│   ├── crispor.py           # CRISPOR guide design + scoring (30s timeout)
│   ├── ensembl.py           # Ensembl REST: gene lookup, sequences, transcripts, orthologs (10s timeout)
│   ├── ncbi.py              # NCBI Entrez via Biopython: gene info, sequences (10s timeout)
│   ├── blast.py             # NCBI BLAST: primer specificity (10s per poll, 60s max wait)
│   └── primer3_api.py       # Primer3 primer design (graceful degradation if primer3-py missing)
└── rpw/                    # Research Pipeline Wrapper (session management layer)
    ├── sessions.py          # Session save/load/resume/export as JSON and Markdown
    ├── protocols.py         # ProtocolGenerator: Markdown protocols with REAGENT_CATALOG (10 Cas systems)
    ├── experiments.py       # ExperimentTracker: log results, history, cross-session comparison
    ├── collaboration.py     # Sharing (token-based), annotations (per-step), PI review (approve/revise/reject)
    ├── audit.py             # Append-only JSONL audit log (every LLM call, workflow event, safety block)
    └── feedback.py          # User feedback collection (Gradio thumbs up/down) + aggregate reports
```

## API Integrations

| Service | What It Does | Endpoint | Timeout | Used In |
|---------|-------------|----------|---------|---------|
| [CRISPOR](http://crispor.tefor.net/) | Guide RNA design + MIT/Doench scoring | `crispor.tefor.net/crispor.py` | 30s | Knockout, off-target scoring |
| [Ensembl REST](https://rest.ensembl.org/) | Gene ID lookup, genomic sequences, transcripts, orthologs | `rest.ensembl.org` | 10s | All workflows (gene resolution, flanking sequence for primers) |
| [NCBI Entrez](https://www.ncbi.nlm.nih.gov/books/NBK25497/) | Gene info, aliases, summaries, sequences | Via Biopython `Bio.Entrez` | 10s | Gene annotation, sequence fetch |
| [NCBI BLAST](https://blast.ncbi.nlm.nih.gov/) | Primer specificity verification (blastn, word_size=7, expect=10) | `blast.ncbi.nlm.nih.gov/Blast.cgi` | 60s total | Validation workflow |
| [Primer3](https://primer3.org/) | PCR primer design (Tm 57-63 C, product 200-500 bp, 3 pairs) | Local via `primer3-py` | N/A | Validation workflow |

All API clients use explicit timeouts and return empty results on failure rather than raising exceptions, so the workflow degrades gracefully if any external service is unavailable.

## Safety & Compliance

Every user message is automatically screened before processing. If a biosafety concern is detected, the workflow is paused and the user receives a safety notice with a recommendation to consult their institutional biosafety committee (IBC).

### Germline Editing Detection

Keyword matching against NIH Guidelines Section III-C and the 2023 Third International Summit on Human Genome Editing. Flags: `human embryo`, `human germline`, `human oocyte`, `human sperm`, `zygote editing`, `heritable genome editing`, `reproductive cloning`, and related terms.

### Select Agent Screening

Checks against the Federal Select Agent Program pathogen list (42 CFR 73). Covers: *Bacillus anthracis*, *Clostridium botulinum*, Ebola virus, Marburg virus, *Yersinia pestis*, variola major/minor, Nipah virus, ricin, SARS-CoV, reconstructed 1918 influenza, and others. Flagged requests note that work with select agents requires registration with the Federal Select Agent Program.

### Dual-Use Research of Concern (DURC)

Keyword matching per USG DURC Policy. Flags: `gain of function`, `enhance transmissibility`, `enhance virulence`, `pandemic potential`, `immune evasion`, `weaponization`, `pathogen enhancement`, `evasion of countermeasures`, `resistance to therapeutics`.

### Sequence Privacy

Before any text reaches an LLM provider, it is scanned for contiguous nucleotide sequences longer than 50 bases (pattern: `[ACGTUacgtu]{50,}`). Short guide RNA sequences (20 bp) pass through; longer sequences that could be patient-derived are blocked with a reference to NIH Genomic Data Sharing Policy (NOT-OD-14-124). This check runs in the LLM provider layer, so it covers all workflows automatically.

## Reagent Catalog

The protocol generator includes catalog references for 10 Cas system variants:

| System | Plasmid | Protein |
|--------|---------|---------|
| SpCas9 | Addgene #42230 (pX330) | IDT Alt-R S.p. Cas9 V3 (Cat# 1081058) |
| SaCas9 | Addgene #61591 (pX601-AAV) | IDT Alt-R S.a. Cas9 (Cat# 10006502) |
| enCas12a | Addgene #132416 (enAsCas12a-HF1) | IDT Alt-R Cas12a Ultra (Cat# 10001272) |
| SpRYCas9 | Addgene #139987 (SpRY-P2A-EGFP) | — |
| CBE (BE4max) | Addgene #110396 | — |
| ABE (ABE7.10) | Addgene #112098 | — |
| PE2 | Addgene #132775 | — |
| PE3 | Addgene #132775 + nicking sgRNA | — |
| dCas9-VP64 | Addgene #61422 (CRISPRa) | — |
| dCas9-KRAB | Addgene #110820 (CRISPRi) | — |

Common reagents: Lipofectamine 3000 (Thermo Fisher L3000001), Lonza 4D-Nucleofector (AAF-1003B), T7 Endonuclease I (NEB M0302S), Puromycin (Sigma P8833).

## Session Management & Collaboration

### Sessions

Every interaction is persisted to disk as JSON. Sessions store the full chat history, workflow state, serialized SessionContext, provider/model info, and timestamps. You can:

- **Resume** a session by loading its ID — the full context (guides, delivery, primers) is restored
- **Export as Markdown** — formatted session report with conversation, timestamps, and metadata
- **List all sessions** — browse by session ID, creation date, and workflow state

### Audit Trail

An append-only JSONL log records every event: `session_started`, `workflow_started`, `llm_call` (with provider, model, latency in ms), `llm_call_error`, `safety_block`, `experiment_result_logged`, `session_shared`, `annotation_added`, `pi_review_requested`, `pi_review_completed`, and `user_feedback`. Each entry includes an ISO timestamp and session ID.

### Collaboration

- **Share sessions** — generate a 12-character token (SHA256-based) that others can use to look up the session
- **Annotations** — add comments to specific workflow steps with author attribution and timestamps
- **PI review** — request review on a session; the PI can approve, request revisions, or reject with comments

### Experiment Tracking

Log wet-lab results linked to sessions using six result types: `editing_efficiency`, `off_target_detected`, `phenotype_confirmed`, `experiment_failed`, `expression_change`, `cell_viability`. Compare results across sessions with Markdown-formatted comparison tables. Filter experiment history by gene and/or species.

## Limitations

This project is in **alpha** (v0.1.0). Known constraints:

- **CRISPOR API availability** — the public CRISPOR API can be slow (30s timeout) or occasionally unavailable; the tool degrades gracefully but guide design will return empty results during downtime
- **No GUI protocol editor** — protocols are exported as Markdown; there is no drag-and-drop visual editor
- **No LIMS integration** — session export is file-based (Markdown / JSON); integration with laboratory information management systems is not yet implemented
- **LLM costs** — each workflow session makes multiple LLM API calls (typically 3-8 per complete workflow); token usage depends on conversation length and model selected
- **No authentication** — session sharing uses tokens but there is no user authentication or access control
- **Primer3 optional** — the `primer3-py` package is listed as a dependency but the validation workflow degrades gracefully if it fails to install on your platform

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (all LLM/API calls are mocked — no keys needed)
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
```

The test suite covers 274 tests across all modules. All LLM calls are mocked at the provider level (`patch("crisprairs.llm.provider.ChatProvider.chat", ...)`), so tests never make real API calls. The `conftest.py` sets dummy API keys and isolates data directories (sessions, audit, experiments) to temp paths.

CI runs on Python 3.10, 3.11, and 3.12 via GitHub Actions on every push and PR to `main`.

## Contributing

Issues and pull requests are welcome. Please run the test suite (`python -m pytest tests/ -v`) and linter (`ruff check src/ tests/`) before submitting.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{moore_crispr_ai_research_suite,
  author    = {Moore, Tim},
  title     = {{CRISPR AI Research Suite}},
  version   = {0.1.0},
  url       = {https://github.com/Tmmoore286/crispr-ai-research-suite},
  license   = {Apache-2.0}
}
```

## License

Apache-2.0 — see [LICENSE](LICENSE).
