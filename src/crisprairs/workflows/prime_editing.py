"""Prime editing workflow: PE2/PE3/PE3b/PEmax modalities."""

from __future__ import annotations

import logging

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.prompts.prime_editing import (
    PROMPT_PROCESS_PEGRNA_DESIGN,
    PROMPT_PROCESS_SYSTEM_SELECTION,
    PROMPT_PROCESS_TARGET,
    PROMPT_REQUEST_ENTRY,
    PROMPT_REQUEST_PEGRNA_DESIGN,
    PROMPT_REQUEST_SYSTEM_SELECTION,
    PROMPT_REQUEST_TARGET,
)

logger = logging.getLogger(__name__)


class PrimeEditingEntry(WorkflowStep):
    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        return StepOutput(result=StepResult.CONTINUE, message=PROMPT_REQUEST_ENTRY)


class PrimeEditingSystemSelect(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_SYSTEM_SELECTION

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_SYSTEM_SELECTION.format(user_message=user_input)
        response = ChatProvider.chat(prompt)
        system = response.get("Answer", "PE2")

        ctx.prime_editor = system
        message = f"Selected prime editing system: **{system}**"
        if system in ("PE3", "PE3b"):
            message += (
                "\n\n*Note: You will also need to design a"
                " nicking sgRNA for the non-edited strand.*"
            )

        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class PrimeEditingTarget(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_TARGET

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_TARGET.format(user_message=user_input)
        response = ChatProvider.chat(prompt)

        ctx.target_gene = response.get("Target gene", "")
        ctx.species = response.get("Species", "human")
        ctx.extra["edit_type"] = response.get("Edit type", "unknown")
        ctx.extra["edit_description"] = response.get("Edit description", "")

        message = (
            f"**Target gene:** {ctx.target_gene}\n"
            f"**Species:** {ctx.species}\n"
            f"**Edit type:** {ctx.extra['edit_type']}\n"
            f"**Edit:** {ctx.extra['edit_description']}\n"
            f"**System:** {ctx.prime_editor}\n\n"
            f"**pegRNA design will require 3 components:**\n"
            f"1. Spacer (20 nt) — positions Cas9 nick near edit site\n"
            f"2. Primer Binding Site (PBS, ~13 nt) — primes RT\n"
            f"3. RT template (~10-30 nt) — encodes the edit"
        )
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class PrimeEditingGuideDesign(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_PEGRNA_DESIGN

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_PEGRNA_DESIGN.format(user_message=user_input)
        response = ChatProvider.chat(prompt)
        choice = response.get("Choice", "no")
        pbs_len = response.get("PBS_length", "13")
        rt_len = response.get("RT_template_length", "15")

        if choice.lower() == "yes":
            message = (
                f"**pegRNA Design Recommendations for {ctx.prime_editor}:**\n\n"
                f"- **PBS length:** {pbs_len} nt (start here, test 10-15 nt range)\n"
                f"- **RT template length:** {rt_len} nt (start here, test 10-25 nt range)\n"
                f"- **Spacer:** Choose 3-5 spacers with NGG PAM within 0-15 nt of edit site\n"
            )
            if ctx.prime_editor in ("PE3", "PE3b"):
                message += (
                    f"\n**Nicking guide design ({ctx.prime_editor}):**\n"
                    f"- Place nick 40-90 bp 3' of the pegRNA-induced nick\n"
                    f"- For PE3b: design the nicking guide to only match the edited sequence\n"
                )
            message += (
                "\n**Recommended tools:**\n"
                "- PrimeDesign: https://primedesign.pinellolab.partners.org/\n"
                "- pegFinder: https://pegfinder.sidichenlab.org/"
            )
        else:
            message = (
                "Understood. Here are resources for prime editing guide design:\n\n"
                "- PrimeDesign: https://primedesign.pinellolab.partners.org/\n"
                "- pegFinder: https://pegfinder.sidichenlab.org/"
            )

        return StepOutput(result=StepResult.DONE, message=message, data=response)
