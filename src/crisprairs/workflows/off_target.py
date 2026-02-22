"""Off-target analysis agent: guide scoring, risk assessment, and reporting."""

from __future__ import annotations

import logging

from crisprairs.engine.context import GuideRNA, SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.prompts.off_target import (
    PROMPT_PROCESS_INPUT,
    PROMPT_PROCESS_REPORT,
    PROMPT_REQUEST_ENTRY,
    PROMPT_REQUEST_INPUT,
    PROMPT_REQUEST_REPORT,
    PROMPT_RISK_ASSESSMENT,
)

logger = logging.getLogger(__name__)


class OffTargetEntry(WorkflowStep):
    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        return StepOutput(result=StepResult.CONTINUE, message=PROMPT_REQUEST_ENTRY)


class OffTargetInput(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_INPUT

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_INPUT.format(user_message=user_input)
        response = ChatProvider.chat(prompt)

        guides_data = response.get("guides", [])
        ctx.species = response.get("species", ctx.species or "human")
        ctx.cas_system = response.get("cas_system", ctx.cas_system or "SpCas9")

        ctx.guides = []
        for g in guides_data:
            ctx.guides.append(GuideRNA(
                sequence=g.get("sequence", ""),
                source="user",
                metadata={"name": g.get("name", "")},
            ))

        message = (
            f"Parsed {len(ctx.guides)} guide(s) for analysis.\n"
            f"**Species:** {ctx.species}\n"
            f"**Cas system:** {ctx.cas_system}"
        )
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class OffTargetScoring(WorkflowStep):
    """Score guides using CRISPOR API and generate risk assessment."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        if not ctx.guides:
            return StepOutput(
                result=StepResult.WAIT_FOR_INPUT,
                message="No guides to analyze. Please provide guide sequences.",
            )

        from crisprairs.apis.crispor import score_existing_guides

        sequences = [g.sequence for g in ctx.guides if g.sequence]
        scoring_results = score_existing_guides(sequences, species=ctx.species)

        # Update guide scores by sequence, not list index.
        scored_by_sequence = {}
        for result in scoring_results:
            seq = result.get("query_sequence", "")
            guides = result.get("guides") or []
            if seq and guides:
                scored_by_sequence[seq] = guides[0]

        for guide in ctx.guides:
            top = scored_by_sequence.get(guide.sequence)
            if not top:
                continue
            guide.score = top.get("mit_specificity_score") or 0.0
            guide.off_target_score = top.get("off_target_count") or 0

        # Generate risk assessment via LLM
        import json

        from crisprairs.llm.provider import ChatProvider

        scoring_str = json.dumps(scoring_results, default=str, indent=2)
        prompt = PROMPT_RISK_ASSESSMENT.format(
            scoring_data=scoring_str,
            genomic_context=f"Species: {ctx.species}, Cas: {ctx.cas_system}",
        )
        assessment = ChatProvider.chat(prompt)

        ctx.off_target_results = assessment.get("assessments", [])

        # Build report
        lines = ["## Off-Target Analysis Report", ""]
        for a in ctx.off_target_results:
            risk = a.get("risk_level", "unknown")
            name = a.get("guide_name", "")
            seq = a.get("sequence", "")
            rec = a.get("recommendation", "")
            lines.append(f"- **{name}** (`{seq}`): **{risk.upper()}** risk — {rec}")

        overall = assessment.get("overall_recommendation", "")
        if overall:
            lines.extend(["", f"**Overall:** {overall}"])

        return StepOutput(
            result=StepResult.CONTINUE,
            message="\n".join(lines),
            data=assessment,
        )


class OffTargetReport(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_REPORT

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_REPORT.format(user_message=user_input)
        response = ChatProvider.chat(prompt)
        choice = response.get("Choice", "no")

        if choice.lower() == "yes":
            message = (
                "**CRISPRitz Deep Analysis Instructions:**\n\n"
                "1. Install using the official repository and docs:\n"
                "   https://github.com/pinellolab/CRISPRitz\n"
                "2. Follow the documented conda/source installation steps.\n"
                "3. Prepare a guide file (one sequence per line).\n"
                "4. Run CRISPRitz search with your reference genome and PAM settings.\n"
                "5. Review output for bulge-tolerant off-targets.\n\n"
                "Off-target analysis complete."
            )
        else:
            message = "Off-target analysis complete."

        return StepOutput(result=StepResult.DONE, message=message, data=response)
