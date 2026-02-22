"""Validation workflow: primer design, BLAST verification, and validation strategy."""

from __future__ import annotations

import logging

from crisprairs.engine.workflow import WorkflowStep, StepOutput, StepResult
from crisprairs.engine.context import SessionContext, PrimerPair
from crisprairs.prompts.validation import (
    PROMPT_REQUEST_VALIDATION_ENTRY,
    PROMPT_REQUEST_PRIMER_DESIGN,
    PROMPT_REQUEST_BLAST,
    PROMPT_PROCESS_BLAST,
)

logger = logging.getLogger(__name__)


class ValidationEntry(WorkflowStep):
    """Display validation strategy overview."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        return StepOutput(result=StepResult.CONTINUE, message=PROMPT_REQUEST_VALIDATION_ENTRY)


class PrimerDesignStep(WorkflowStep):
    """Design PCR primers flanking the CRISPR target."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        target_sequence = self._fetch_target_sequence(ctx)
        if not target_sequence:
            return StepOutput(
                result=StepResult.CONTINUE,
                message=(
                    "Could not fetch target sequence for primer design. "
                    "You can design primers manually using Primer3 "
                    "(https://primer3.ut.ee/)."
                ),
            )

        target_seq, target_start, target_length = target_sequence
        from crisprairs.apis.primer3_api import design_primers

        pairs = design_primers(target_seq, target_start, target_length)

        if not pairs:
            return StepOutput(
                result=StepResult.CONTINUE,
                message="Primer design returned no results. primer3-py may not be installed.",
            )

        ctx.primers = []
        lines = [PROMPT_REQUEST_PRIMER_DESIGN, "", "| Pair | Forward | Reverse | Tm(F) | Tm(R) | Size |",
                 "|------|---------|---------|-------|-------|------|"]
        for i, p in enumerate(pairs, 1):
            ctx.primers.append(PrimerPair(
                forward=p["forward_seq"],
                reverse=p["reverse_seq"],
                product_size=p["product_size"],
                tm_forward=p["forward_tm"],
                tm_reverse=p["reverse_tm"],
            ))
            lines.append(
                f"| {i} | `{p['forward_seq']}` | `{p['reverse_seq']}` | "
                f"{p['forward_tm']} | {p['reverse_tm']} | {p['product_size']} |"
            )

        return StepOutput(result=StepResult.CONTINUE, message="\n".join(lines))

    @staticmethod
    def _fetch_target_sequence(ctx: SessionContext):
        """Fetch genomic sequence around the target for primer design."""
        if not ctx.target_gene or not ctx.species:
            return None
        try:
            from crisprairs.apis.ensembl import lookup_gene_id, get_sequence

            gene_id = lookup_gene_id(ctx.target_gene, ctx.species)
            if not gene_id:
                return None
            seq_data = get_sequence(gene_id, expand_bp=500)
            if not seq_data:
                return None
            full_seq = seq_data.get("full_sequence", "")
            if len(full_seq) < 200:
                return None
            # Place target in middle
            mid = len(full_seq) // 2
            return (full_seq, mid - 10, 23)
        except Exception as e:
            logger.error("Target sequence fetch failed: %s", e)
            return None


class BlastCheckStep(WorkflowStep):
    """Optional BLAST primer specificity verification."""

    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_BLAST

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_BLAST.format(user_message=user_input)
        response = ChatProvider.chat(prompt)
        choice = response.get("Choice", "no")

        if choice.lower() != "yes" or not ctx.primers:
            return StepOutput(
                result=StepResult.DONE,
                message="Skipping BLAST verification. Validation workflow complete.",
                data=response,
            )

        # Run BLAST on first primer pair
        primer = ctx.primers[0]
        from crisprairs.apis.blast import check_primer_specificity

        blast_result = check_primer_specificity(
            primer.forward, primer.reverse, organism=ctx.species
        )

        primer.blast_status = "specific" if blast_result["specific"] else "non-specific"

        if blast_result["specific"]:
            message = (
                "**BLAST Result: Primers are specific.**\n\n"
                f"Forward primer: {blast_result['forward_hits']} hit(s)\n"
                f"Reverse primer: {blast_result['reverse_hits']} hit(s)\n\n"
                "Validation workflow complete."
            )
        else:
            message = (
                "**BLAST Result: Primers may not be specific.**\n\n"
                f"Forward primer: {blast_result['forward_hits']} hit(s)\n"
                f"Reverse primer: {blast_result['reverse_hits']} hit(s)\n\n"
                "Consider redesigning primers or using a different pair."
            )

        return StepOutput(result=StepResult.DONE, message=message, data=blast_result)
