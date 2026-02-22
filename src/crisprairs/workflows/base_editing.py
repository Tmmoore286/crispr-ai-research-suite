"""Base editing workflow: CBE (C>T) and ABE (A>G) editing modalities."""

from __future__ import annotations

import logging

from crisprairs.engine.workflow import WorkflowStep, StepOutput, StepResult
from crisprairs.engine.context import SessionContext
from crisprairs.prompts.base_editing import (
    PROMPT_REQUEST_ENTRY,
    PROMPT_REQUEST_SYSTEM_SELECTION,
    PROMPT_PROCESS_SYSTEM_SELECTION,
    PROMPT_REQUEST_TARGET,
    PROMPT_PROCESS_TARGET,
    PROMPT_REQUEST_GUIDE_DESIGN,
    PROMPT_PROCESS_GUIDE_DESIGN,
)

logger = logging.getLogger(__name__)


class BaseEditingEntry(WorkflowStep):
    """Display base editing introduction."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        return StepOutput(result=StepResult.CONTINUE, message=PROMPT_REQUEST_ENTRY)


class BaseEditingSystemSelect(WorkflowStep):
    """Select CBE, ABE, or Dual base editor."""

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
        system = response.get("Answer", "CBE")

        ctx.base_editor = system
        message = f"Selected base editing system: **{system}**"
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class BaseEditingTarget(WorkflowStep):
    """Collect target gene and desired base change."""

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
        ctx.target_base_change = response.get("Base change", "")

        warning = ""
        if ctx.base_editor == "CBE" and "A>G" in ctx.target_base_change:
            warning = "\n\n**Note:** You selected CBE but described an A>G change. CBE performs C>T. Consider switching to ABE."
        elif ctx.base_editor == "ABE" and "C>T" in ctx.target_base_change:
            warning = "\n\n**Note:** You selected ABE but described a C>T change. ABE performs A>G. Consider switching to CBE."

        window = "4-8" if ctx.base_editor == "CBE" else "4-7"
        message = (
            f"**Target gene:** {ctx.target_gene}\n"
            f"**Species:** {ctx.species}\n"
            f"**Desired change:** {ctx.target_base_change}\n"
            f"**Editing window:** Positions {window} of protospacer"
            f"{warning}"
        )
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class BaseEditingGuideDesign(WorkflowStep):
    """Guide RNA design with editing window constraints."""

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

        system = ctx.base_editor or "CBE"
        window = "4-8" if system == "CBE" else "4-7"

        if choice.lower() == "yes":
            message = (
                f"Guide RNA design parameters for {system} base editing:\n\n"
                f"- Editing window: positions {window}\n"
                f"- Target gene: {ctx.target_gene}\n"
                f"- PAM: NGG (SpCas9-based)\n\n"
                f"**Recommended resources for base editing guide design:**\n"
                f"- BE-Designer: http://www.rgenome.net/be-designer/\n"
                f"- BE-Hive: https://modelseed.org/be-hive/\n"
                f"- CRISPRscan: https://www.crisprscan.org/"
            )
        else:
            message = (
                "Understood. Here are resources for manual base editing guide design:\n\n"
                "- BE-Designer: http://www.rgenome.net/be-designer/\n"
                "- BE-Hive prediction: https://modelseed.org/be-hive/"
            )

        return StepOutput(result=StepResult.DONE, message=message, data=response)
