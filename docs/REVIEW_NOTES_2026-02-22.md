# CRISPR AI Research Suite Review Notes (2026-02-22)

## Code Review Findings (No Changes Made)

1. **High: Session chat persistence is incompatible with current Gradio history format.**
   `chat_respond` saves history as dict messages, but `SessionManager.save` only correctly serializes tuple/list pairs; dicts are stored as `"role": "unknown"`, which degrades export/restore fidelity.
   - `crispr-ai-research-suite/src/crisprairs/app.py:295`
   - `crispr-ai-research-suite/src/crisprairs/rpw/sessions.py:48`
   - `crispr-ai-research-suite/src/crisprairs/rpw/sessions.py:62`

2. **High: Audit logging can cross-contaminate sessions in multi-user usage.**
   `AuditLog` keeps one global `_session_id` for the entire process. Any concurrent session can overwrite it, causing events to be logged to the wrong file.
   - `crispr-ai-research-suite/src/crisprairs/rpw/audit.py:18`
   - `crispr-ai-research-suite/src/crisprairs/rpw/audit.py:23`
   - `crispr-ai-research-suite/src/crisprairs/app.py:123`

3. **Medium: `fetch_gene_sequence` likely uses incorrect Entrez object type.**
   It calls `Entrez.efetch(db="nucleotide", id=<gene_id>)` with an NCBI Gene ID; nucleotide DB expects nucleotide accession/UID, not gene UID.
   - `crispr-ai-research-suite/src/crisprairs/apis/ncbi.py:95`
   - `crispr-ai-research-suite/src/crisprairs/apis/ncbi.py:109`

4. **Medium: Off-target score assignment can map to the wrong guide.**
   Scoring filters empty sequences before API call, then writes results back by index into the original guide list, which can shift mappings.
   - `crispr-ai-research-suite/src/crisprairs/workflows/off_target.py:73`
   - `crispr-ai-research-suite/src/crisprairs/workflows/off_target.py:77`

5. **Medium: CRISPRitz install guidance appears incorrect.**
   Workflow says `pip install crispritz`; upstream project documentation points to source/conda workflows, not pip as the canonical path.
   - `crispr-ai-research-suite/src/crisprairs/workflows/off_target.py:136`

6. **Medium: “New Session” UX clears chat but puts welcome text into input box.**
   This likely produces confusing behavior after reset.
   - `crispr-ai-research-suite/src/crisprairs/app.py:325`
   - `crispr-ai-research-suite/src/crisprairs/app.py:377`

7. **Medium (product gap): README claims exceed what UI currently exposes.**
   README claims resume/collaboration/experiment tracking as user-facing capabilities, but app UI only exposes Chat/Protocol Export/Session Export tabs.
   - `crispr-ai-research-suite/README.md:24`
   - `crispr-ai-research-suite/README.md:25`
   - `crispr-ai-research-suite/README.md:26`
   - `crispr-ai-research-suite/src/crisprairs/app.py:346`
   - `crispr-ai-research-suite/src/crisprairs/app.py:383`
   - `crispr-ai-research-suite/src/crisprairs/app.py:393`

8. **Low: Protocol export defaults unknown modalities to “Knockout.”**
   Off-target/troubleshoot exports can be mislabeled and include irrelevant steps.
   - `crispr-ai-research-suite/src/crisprairs/rpw/protocols.py:138`

9. **Test gap: Key regressions above are not currently tested (`dict`-history persistence, `fetch_gene_sequence`).**
   - `crispr-ai-research-suite/tests/test_rpw/test_sessions.py:13`
   - `crispr-ai-research-suite/tests/test_apis/test_ncbi.py:7`

Validation run:
- `python3 -m pytest -q -p no:cacheprovider` -> `274 passed, 1 skipped`.

---

## CRISPR Community Context (as of February 22, 2026)

Tools like this do exist, but mostly as specialized components rather than one assistant covering full workflow:

- Guide design/scoring: CRISPOR, CHOPCHOP.
- Prime editing design: PrimeDesign.
- Outcome quantification: CRISPResso2.
- Off-target (including variant-aware and bulges): CRISPRme, CRISPRitz, newer variant-aware Cas-OFFinder work.
- AI-specific design/risk models are accelerating (for example CCLMoff-type work).
- Closest conceptual neighbor: CRISPR-GPT (Nature BME, 2025), which already frames conversational CRISPR design support.

---

## Is This Tool Useful for Research?

Yes, with caveats.
Most labs still stitch multiple tools manually; this suite is useful if it acts as a reliable orchestration layer that improves reproducibility and documentation. The architecture points in that direction, but current reliability/implementation gaps reduce trust for research operations.

---

## What This Tool Can Do Differently (If Tightened)

- Unified conversational flow across modality selection, design, delivery, validation, and report export.
- Built-in safety/privacy/audit controls in one interface.
- Session plus lab-process metadata in one artifact stream.

This combination is uncommon in a single open-source package, even though component capabilities exist elsewhere.

---

## Highest-Value Improvements

1. Fix session/audit correctness first (history serialization, per-session logging isolation).
2. Add deterministic validators before LLM parsing (guide format/length/PAM/species checks).
3. Integrate variant-aware off-target engines directly (CRISPRme/Cas-OFFinder class), not just mention them.
4. Replace advisory-only prime/base workflows with actual design computation paths (PrimeDesign/BE models integration).
5. Align README claims with shipped UI, or expose missing modules in UI/API.
6. Add evidence benchmarks against established toolchains (accuracy, time-to-protocol, reproducibility metrics).
