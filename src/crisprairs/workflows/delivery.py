"""Delivery method selection workflow for all CRISPR modalities."""

from __future__ import annotations

import logging

from crisprairs.engine.context import DeliveryInfo, SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.prompts.delivery import (
    PROMPT_PROCESS_SELECT,
    PROMPT_REQUEST_ENTRY,
    PROMPT_REQUEST_SELECT,
)

logger = logging.getLogger(__name__)


class DeliveryEntry(WorkflowStep):
    """Display delivery method introduction with experiment context."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        text = PROMPT_REQUEST_ENTRY

        context_lines = []
        if ctx.modality:
            context_lines.append(f"**Current workflow:** {ctx.modality}")
        if ctx.cas_system:
            context_lines.append(f"**CRISPR system:** {ctx.cas_system}")
        if ctx.target_gene:
            context_lines.append(f"**Target gene:** {ctx.target_gene}")
        if ctx.species:
            context_lines.append(f"**Species:** {ctx.species}")

        if context_lines:
            text += "\n**Your experiment context:**\n" + "\n".join(context_lines) + "\n"

        if ctx.cas_system == "SaCas9":
            text += (
                "\n*Note: SaCas9 is compact enough for AAV"
                " packaging — consider AAV delivery"
                " for in vivo applications.*\n"
            )
        elif ctx.cas_system and "Cas12a" in ctx.cas_system:
            text += "\n*Note: Cas12a systems work well with both RNP and plasmid delivery.*\n"

        return StepOutput(result=StepResult.CONTINUE, message=text)


class DeliverySelect(WorkflowStep):
    """Collect cell type and preferences, recommend delivery method."""

    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_SELECT

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_SELECT.format(user_message=user_input)
        response = ChatProvider.chat(prompt)

        method = response.get("delivery_method", "lipofection")
        fmt = response.get("format", "plasmid")
        reasoning = response.get("reasoning", "")
        product = response.get("specific_product", "")
        alternatives = response.get("alternatives", "")

        ctx.delivery = DeliveryInfo(
            method=method,
            format=fmt,
            product=product,
            reasoning=reasoning,
            alternatives=alternatives,
        )

        message = (
            f"**Recommended delivery method:** {method}\n"
            f"**Format:** {fmt}\n"
            f"**Specific product:** {product}\n\n"
            f"**Reasoning:** {reasoning}\n"
        )
        if alternatives:
            message += f"\n**Alternative:** {alternatives}\n"

        return StepOutput(result=StepResult.DONE, message=message, data=response)
