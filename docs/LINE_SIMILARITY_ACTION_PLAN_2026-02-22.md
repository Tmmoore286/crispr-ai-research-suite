# Line Similarity Audit + Action Plan (2026-02-22)

Scope:
- Compared `crispr-ai-research-suite` implementation files against `crispr-gpt-pub` using stricter line-based metrics:
  - normalized line-sequence similarity (`difflib` on non-empty non-comment lines)
  - unique-line overlap ratio
  - longest contiguous matching block size
- Full machine-readable output:
  - `docs/line_similarity_audit_2026-02-22.json`

Summary:
- Files analyzed: `40`
- High similarity: `15`
- Medium similarity: `1`

## Highest Similarity Targets

### Tier 1: Rewrite First (Very High Similarity)

1. `src/crisprairs/rpw/feedback.py` -> best match `crispr-gpt-pub/rpw/feedback.py`
   - `seq_ratio=0.9468`, `longest_block=74 lines`
2. `src/crisprairs/rpw/audit.py` -> `crispr-gpt-pub/rpw/audit.py`
   - `seq_ratio=0.9134`, `longest_block=31 lines`
3. `src/crisprairs/rpw/collaboration.py` -> `crispr-gpt-pub/rpw/collaboration.py`
   - `seq_ratio=0.9003`, `longest_block=56 lines`
4. `src/crisprairs/rpw/experiments.py` -> `crispr-gpt-pub/rpw/experiments.py`
   - `seq_ratio=0.8978`, `longest_block=37 lines`
5. `src/crisprairs/rpw/sessions.py` -> `crispr-gpt-pub/rpw/sessions.py`
   - `seq_ratio=0.8339`, `longest_block=47 lines`

Recommended changes:
- Reimplement each module from a fresh design, not incremental edits.
- Change data models and API surfaces (function/class interfaces), not just wording.
- Replace token/session/collaboration schemas with newly defined structures.
- Add fresh tests that assert behavior without mirroring old test scenarios line-for-line.

### Tier 1b: Prompt Layer (High Similarity to old constant prompt files)

6. `src/crisprairs/prompts/troubleshoot.py` -> `crispr-gpt-pub/crisprgpt/troubleshoot_constant.py`
   - `seq_ratio=0.9337`, `longest_block=100 lines`
7. `src/crisprairs/prompts/prime_editing.py` -> `crispr-gpt-pub/crisprgpt/prime_editing_constant.py`
   - `seq_ratio=0.8856`, `longest_block=28 lines`
8. `src/crisprairs/prompts/activation_repression.py` -> `crispr-gpt-pub/crisprgpt/act_rep_constant.py`
   - `seq_ratio=0.8471`, `longest_block=27 lines`
9. `src/crisprairs/prompts/off_target.py` -> `crispr-gpt-pub/crisprgpt/off_target_agent_constant.py`
   - `seq_ratio=0.8025`, `longest_block=20 lines`
10. `src/crisprairs/prompts/validation.py` -> `crispr-gpt-pub/crisprgpt/validation_constant.py`
   - `seq_ratio=0.7816`, `longest_block=15 lines`
11. `src/crisprairs/prompts/base_editing.py` -> `crispr-gpt-pub/crisprgpt/base_editing_constant.py`
   - `seq_ratio=0.7571`, `longest_block=15 lines`
12. `src/crisprairs/prompts/delivery.py` -> `crispr-gpt-pub/crisprgpt/delivery_constant.py`
   - `seq_ratio=0.7021`, `longest_block=12 lines`

Recommended changes:
- Re-author prompts from scratch with:
  - different instruction ordering and decomposition
  - different JSON schema keys
  - different examples and rationale text
- Move prompt construction into composable builders (not large static constant blocks).
- Add deterministic validators that reduce dependency on prompt exact phrasing.

### Tier 2: API and Provider Modules (Moderate-to-High Similarity)

13. `src/crisprairs/apis/blast.py` -> `crispr-gpt-pub/crisprgpt/apis/blast.py`
   - `seq_ratio=0.8360`, `longest_block=26 lines`
14. `src/crisprairs/apis/primer3_api.py` -> `crispr-gpt-pub/crisprgpt/apis/primer3_api.py`
   - `seq_ratio=0.6475`, `longest_block=14 lines`
15. `src/crisprairs/llm/provider.py` -> `crispr-gpt-pub/rpw/providers.py`
   - `seq_ratio=0.5212`, `longest_block=23 lines`

Recommended changes:
- For API clients, refactor transport/runtime shape:
  - introduce typed request/response dataclasses
  - centralize retry/timeouts/error policy
  - rework function boundaries to be domain-first (not endpoint-first)
- For provider layer, split into provider-specific adapters behind a protocol and add explicit request/response objects.

### Tier 3: Lower Similarity (Monitor, not urgent)

- `src/crisprairs/rpw/protocols.py` (`seq_ratio=0.5043`, but large file and shared domain wording expected)
- `src/crisprairs/apis/ensembl.py`, `src/crisprairs/apis/ncbi.py`, `src/crisprairs/apis/crispor.py` are materially lower and may only need selective refactors.

## Suggested Execution Order

1. Rebuild `rpw/` modules first (highest similarity + contains existing functional bugs).
2. Re-author all high-similarity prompt files.
3. Refactor `blast.py`, `primer3_api.py`, and `llm/provider.py` to new abstractions.
4. Add CI guardrail:
   - fail build if any file exceeds thresholds against a blocked-source snapshot.

## CI Similarity Guardrail (Recommended Thresholds)

- `seq_ratio >= 0.80` OR `longest_block_lines >= 25` => fail
- `seq_ratio >= 0.65` => warning requiring manual review

## Notes

- This is a structural similarity audit, not legal advice.
- High similarity can occur from constrained domains; still, the listed files are the most likely places to reduce lineage risk by reimplementation.
