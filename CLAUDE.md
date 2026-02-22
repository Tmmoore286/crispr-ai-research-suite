# CLAUDE.md — CRISPR AI Research Suite

## Project Overview

CRISPR AI Research Suite is an **original, Apache-2.0 licensed** AI-assisted platform for designing CRISPR experiments. It guides researchers from target gene selection through guide RNA design, delivery method optimization, validation strategy, and protocol export — producing bench-ready experimental plans.

This is a **100% original codebase**. All implementations are written from scratch or adapted from our own prior work. Scientific knowledge (CRISPR mechanisms, public APIs, bioinformatics concepts) comes from published literature.

**Package:** `crispr-ai-research-suite` (import as `crisprairs`)
**License:** Apache-2.0
**Author:** Tim Moore

## Quick Reference

```bash
# Run tests (no API keys needed — all LLM/API calls are mocked)
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_engine/ -v

# Lint
ruff check src/ tests/

# Run the app (requires API key in .env)
python -m crisprairs.app
```

## Architecture

```
src/crisprairs/
├── app.py                  # Gradio UI entry point
├── engine/                 # Pipeline execution engine
│   ├── workflow.py          # WorkflowStep ABC, StepOutput, StepResult, Router
│   ├── context.py           # SessionContext dataclass (typed session state)
│   └── runner.py            # PipelineRunner (advances steps, manages flow)
├── llm/                    # LLM provider abstraction
│   ├── provider.py          # OpenAI + Anthropic backends, ChatProvider router
│   └── parser.py            # JSON extraction, markdown fence stripping
├── safety/                 # Biosafety and privacy checks
│   ├── biosafety.py         # Germline/pathogen/dual-use checks (NIH/WHO guidelines)
│   └── privacy.py           # Identifiable genomic sequence detection
├── workflows/              # CRISPR experiment workflow steps
│   ├── knockout.py          # Gene knockout via runtime CRISPOR API
│   ├── base_editing.py      # CBE/ABE base editing
│   ├── prime_editing.py     # PE2/PE3/PEmax prime editing
│   ├── activation_repression.py  # CRISPRa/CRISPRi
│   ├── off_target.py        # Off-target analysis agent
│   ├── delivery.py          # Delivery method selection
│   ├── validation.py        # Validation + primer design + BLAST
│   ├── troubleshoot.py      # Troubleshooting failed experiments
│   └── automation.py        # Safe protocol automation
├── prompts/                # LLM prompt templates
│   ├── cas_selection.py     # Cas protein selection prompts
│   ├── knockout.py          # Knockout workflow prompts
│   ├── common.py            # Shared prompt utilities
│   └── ...                  # One file per workflow module
├── apis/                   # External API clients
│   ├── ncbi.py              # NCBI Entrez via Biopython
│   ├── ensembl.py           # Ensembl REST API
│   ├── crispor.py           # CRISPOR guide scoring
│   ├── blast.py             # NCBI BLAST
│   └── primer3_api.py       # Primer3 primer design
└── rpw/                    # Research Pipeline Wrapper (session management layer)
    ├── audit.py             # Append-only JSONL audit logging
    ├── sessions.py          # Session persistence and resume
    ├── protocols.py         # Protocol Markdown generation
    ├── experiments.py       # Experiment result tracking
    ├── collaboration.py     # Sharing, annotations, PI review
    └── feedback.py          # User feedback collection
```

## Key Design Decisions

### Pipeline/Step Engine (replaces state machine)
- **`WorkflowStep`** is an abstract base class. Each step is a callable with a typed `SessionContext`.
- **`StepResult`** enum: `CONTINUE`, `WAIT_FOR_INPUT`, `DONE`, `BRANCH`.
- **`PipelineRunner`** advances through step sequences, handles user input collection, and manages branching between workflows.
- **`SessionContext`** is a typed dataclass replacing untyped memory dicts. Fields: `target_gene`, `species`, `modality`, `cas_system`, `guides`, `delivery`, `primers`, etc.

### LLM Provider
- Direct `openai` SDK for OpenAI (no langchain).
- Direct `anthropic` SDK for Anthropic.
- `ChatProvider` routes based on `LLM_PROVIDER` env var.
- All calls go through audit logging.

### Safety
- Biosafety checks from **published NIH/WHO guidelines** and the **Federal Select Agent Program**.
- Privacy checks for identifiable genomic sequences.
- Runs automatically before LLM calls.

### Workflows
- Each workflow module contains `WorkflowStep` subclasses.
- Knockout uses **runtime CRISPOR API** for guide design (not bundled sgRNA libraries).
- All other workflows: base editing, prime editing, CRISPRa/i, off-target, delivery, validation, troubleshooting.

## Development Workflow

### Commit discipline
1. **Commit after each significant change.** One logical unit per commit.
2. **Write tests alongside or before implementation.** Every module gets tests.
3. **Run the full test suite before committing:**
   ```bash
   python -m pytest tests/ -v
   ```
   All tests must pass. Do not commit with failing tests.
4. **Lint before committing:**
   ```bash
   ruff check src/ tests/
   ```
5. **Commit message format:** Imperative mood, concise. Examples:
   - `Add pipeline execution engine with step/context/runner`
   - `Add delivery method selection workflow`

### Adding a new workflow — checklist
- [ ] Create `src/crisprairs/workflows/new_module.py` with `WorkflowStep` subclasses
- [ ] Create `src/crisprairs/prompts/new_module.py` with prompt templates
- [ ] Create `tests/test_workflows/test_new_module.py` with mocked LLM calls
- [ ] Run `python -m pytest tests/ -v` — all green
- [ ] Register steps in `Router` if needed
- [ ] Commit

### Testing patterns
- **All LLM calls are mocked.** Never make real API calls in tests.
- **Mock at the source module:** `patch("crisprairs.llm.provider.ChatProvider.chat", ...)`
- **Use `SessionContext`** for typed test state instead of raw dicts.
- **conftest.py** sets dummy API keys and isolates data directories.

### API client patterns
- Graceful degradation: missing optional deps return empty results, not exceptions.
- All HTTP requests use explicit timeouts (10s default).
- Pure functions: no side effects on session state.

## Environment
- **Python 3.10+** (3.11+ recommended)
- **API keys:** Set in `.env` (copy from `.env.example`). Tests do not require API keys.
- **Optional:** `primer3-py` — validation workflow degrades gracefully without it.

## What This Project Is NOT
- This is **not** a fork of any existing CRISPR tool.
- This does **not** use bundled sgRNA libraries — all guide design is done via runtime API calls.
- This does **not** depend on langchain — LLM calls use provider SDKs directly.
