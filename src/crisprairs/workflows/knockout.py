"""Knockout workflow: gene knockout via runtime CRISPOR guide design.

Unlike bundled sgRNA libraries, this workflow queries the CRISPOR API
at runtime to design and score guide RNAs for any gene in any supported
organism. This provides broader coverage and always-current scoring.
"""

from __future__ import annotations

import logging

from crisprairs.engine.context import GuideRNA, SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.prompts.knockout import (
    PROMPT_PROCESS_GUIDE_SELECTION,
    PROMPT_PROCESS_TARGET_INPUT,
    PROMPT_REQUEST_GUIDE_REVIEW,
    PROMPT_REQUEST_TARGET_INPUT,
)

logger = logging.getLogger(__name__)


class KnockoutTargetInput(WorkflowStep):
    """Collect target gene and species from the user."""

    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_TARGET_INPUT

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_TARGET_INPUT.format(user_message=user_input)
        response = ChatProvider.chat(prompt)

        ctx.target_gene = response.get("Target gene", "")
        ctx.species = response.get("Species", "human")
        ctx.cas_system = ctx.cas_system or "SpCas9"
        ctx.extra["preferred_exon"] = response.get("Preferred exon", "early constitutive")

        message = (
            f"**Target gene:** {ctx.target_gene}\n"
            f"**Species:** {ctx.species}\n"
            f"**Cas system:** {ctx.cas_system}\n"
            f"**Strategy:** Target {ctx.extra.get('preferred_exon', 'early constitutive')} exons"
        )

        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class KnockoutGuideDesign(WorkflowStep):
    """Design guide RNAs using the CRISPOR API (or Ensembl + CRISPOR pipeline)."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        gene = ctx.target_gene
        species = ctx.species

        if not gene:
            return StepOutput(
                result=StepResult.WAIT_FOR_INPUT,
                message="No target gene specified. Please provide a gene symbol.",
            )

        # Step 1: Fetch genomic sequence from Ensembl
        from crisprairs.apis.ensembl import get_sequence, lookup_gene_id

        gene_id = lookup_gene_id(gene, species)
        sequence = None
        if gene_id:
            seq_data = get_sequence(gene_id)
            if seq_data:
                sequence = seq_data.get("full_sequence", "")

        # Step 2: Design guides via CRISPOR
        guides = []
        if sequence and len(sequence) >= 100:
            from crisprairs.apis.crispor import design_guides

            target_seq = sequence[:1000] if len(sequence) > 1000 else sequence
            crispor_results = design_guides(target_seq, species=species)

            for g in crispor_results[:10]:
                guides.append(GuideRNA(
                    sequence=g.get("guide_sequence", ""),
                    pam=g.get("pam", "NGG"),
                    score=g.get("mit_specificity_score") or 0.0,
                    off_target_score=g.get("off_target_count") or 0,
                    source="crispor",
                    metadata={
                        "doench2016": g.get("doench2016_score"),
                        "position": g.get("position", ""),
                    },
                ))

        ctx.guides = guides

        if not guides:
            message = (
                f"Could not retrieve guide RNA candidates for **{gene}** ({species}). "
                "This may be due to API availability. You can try again or provide "
                "guide sequences manually."
            )
        else:
            lines = [
                PROMPT_REQUEST_GUIDE_REVIEW,
                "",
                "| # | Sequence | MIT Score | Off-targets |",
                "|---|----------|-----------|-------------|",
            ]
            for i, g in enumerate(guides[:5], 1):
                lines.append(
                    f"| {i} | `{g.sequence}` | {g.score:.1f} | {int(g.off_target_score)} |"
                )
            message = "\n".join(lines)

        return StepOutput(result=StepResult.CONTINUE, message=message)


class KnockoutGuideSelection(WorkflowStep):
    """Let the user review and select guide RNAs."""

    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return "Please select guides to proceed with, or type 'all' to use top-ranked guides."

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_GUIDE_SELECTION.format(user_message=user_input)
        response = ChatProvider.chat(prompt)

        selection = response.get("Selection", "top3")
        if selection == "all" or selection == "top3":
            ctx.selected_guide_index = 0  # Use top guides
        else:
            ctx.selected_guide_index = 0

        selected = ctx.guides[:3] if ctx.guides else []
        if selected:
            msg = f"Selected {len(selected)} guide(s) for knockout of **{ctx.target_gene}**."
        else:
            msg = (
                "No guides available. Please provide sequences"
                " manually or try a different target."
            )

        return StepOutput(result=StepResult.DONE, message=msg, data=response)
