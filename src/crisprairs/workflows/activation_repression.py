"""CRISPRa/CRISPRi (activation/repression) workflow."""

from __future__ import annotations

import logging

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.prompts.activation_repression import (
    PROMPT_PROCESS_GUIDE_DESIGN,
    PROMPT_PROCESS_SYSTEM_SELECTION,
    PROMPT_PROCESS_TARGET,
    PROMPT_REQUEST_ENTRY,
    PROMPT_REQUEST_GUIDE_DESIGN,
    PROMPT_REQUEST_SYSTEM_SELECTION,
    PROMPT_REQUEST_TARGET,
)

logger = logging.getLogger(__name__)


class ActRepEntry(WorkflowStep):
    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        return StepOutput(result=StepResult.CONTINUE, message=PROMPT_REQUEST_ENTRY)


class ActRepSystemSelect(WorkflowStep):
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

        ctx.effector_system = response.get("Answer", "dCas9-VP64")
        mode = response.get("Mode", "activation")
        ctx.modality = f"{'activation' if mode == 'activation' else 'repression'}"

        message = f"Selected system: **{ctx.effector_system}** ({mode})"
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class ActRepTarget(WorkflowStep):
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
        ctx.target_region = response.get("TSS targeting note", "")

        message = (
            f"**Target gene:** {ctx.target_gene}\n"
            f"**Species:** {ctx.species}\n"
            f"**System:** {ctx.effector_system}\n"
            f"**TSS targeting:** {ctx.target_region}"
        )
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class ActRepGuideDesign(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_GUIDE_DESIGN

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_GUIDE_DESIGN.format(user_message=user_input)
        response = ChatProvider.chat(prompt)
        choice = response.get("Choice", "no")

        if choice.lower() == "yes":
            message = (
                f"Guide design recommendations for {ctx.effector_system}:\n\n"
                f"- Target gene: {ctx.target_gene}\n"
                f"- Use 2-5 guides per gene for robust effects\n\n"
                f"**Recommended tools:**\n"
                f"- CRISPick (Broad Institute)\n"
                f"- CHOPCHOP CRISPRa/CRISPRi mode"
            )
        else:
            message = "Understood. Proceeding without automated guide design."

        return StepOutput(result=StepResult.DONE, message=message, data=response)
