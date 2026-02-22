# CRISPR AI Research Suite

AI-assisted platform for designing CRISPR experiments — from target gene selection through guide RNA design, delivery method optimization, validation strategy, and protocol export.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Knockout** — Gene knockout via runtime CRISPOR guide RNA design
- **Base Editing** — CBE (C>T) and ABE (A>G) point mutations
- **Prime Editing** — PE2/PE3/PEmax precise insertions, deletions, and substitutions
- **CRISPRa/CRISPRi** — Gene activation and repression
- **Off-Target Analysis** — Guide scoring and risk assessment
- **Delivery Optimization** — Method selection based on cell type and experiment
- **Validation Strategy** — Primer design, BLAST verification
- **Troubleshooting** — Diagnose and fix failed experiments
- **Protocol Export** — Bench-ready Markdown protocols with reagent details
- **Session Management** — Save, resume, export, and share sessions
- **Collaboration** — Annotations, PI review workflows

## Quick Start

```bash
# Clone
git clone https://github.com/Tmmoore286/crispr-ai-research-suite.git
cd crispr-ai-research-suite

# Install (core library)
pip install -e .

# Install with UI (requires Python 3.10+)
pip install -e ".[ui]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run the UI
python -m crisprairs.app
```

The app will launch at `http://localhost:7860`.

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `openai` or `anthropic` |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `NCBI_EMAIL` | Recommended | Email for NCBI Entrez API |
| `NCBI_API_KEY` | Optional | NCBI API key for higher rate limits |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
```

## Architecture

```
src/crisprairs/
├── app.py              # Gradio UI
├── engine/             # Pipeline execution engine
├── llm/                # LLM provider abstraction (OpenAI + Anthropic)
├── safety/             # Biosafety and privacy checks
├── workflows/          # CRISPR experiment workflow steps
├── prompts/            # LLM prompt templates
├── apis/               # External API clients (NCBI, Ensembl, CRISPOR, BLAST, Primer3)
└── rpw/                # Session management, audit, protocols, collaboration
```

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation and development guidelines.

## License

Apache-2.0 — see [LICENSE](LICENSE).
