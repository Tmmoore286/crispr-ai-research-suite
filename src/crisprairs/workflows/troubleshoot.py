"""Troubleshooting workflow for failed CRISPR experiments."""

from __future__ import annotations

import json
import logging

from crisprairs.engine.context import SessionContext
from crisprairs.engine.workflow import StepOutput, StepResult, WorkflowStep
from crisprairs.prompts.troubleshoot import (
    PROMPT_PROCESS_TROUBLESHOOT_ADVISE,
    PROMPT_PROCESS_TROUBLESHOOT_DIAGNOSE,
    PROMPT_PROCESS_TROUBLESHOOT_ENTRY,
    PROMPT_REQUEST_TROUBLESHOOT_DIAGNOSE,
    PROMPT_REQUEST_TROUBLESHOOT_ENTRY,
    TROUBLESHOOT_KNOWLEDGE,
)

logger = logging.getLogger(__name__)


class TroubleshootEntry(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_TROUBLESHOOT_ENTRY

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        prompt = PROMPT_PROCESS_TROUBLESHOOT_ENTRY.format(user_message=user_input)
        response = ChatProvider.chat(prompt)

        category = response.get("Category", "other")
        summary = response.get("Summary", "")

        ctx.troubleshoot_issue = category
        ctx.extra["troubleshoot_summary"] = summary

        message = f"**Issue category:** {category}\n**Summary:** {summary}"
        return StepOutput(result=StepResult.CONTINUE, message=message, data=response)


class TroubleshootDiagnose(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return PROMPT_REQUEST_TROUBLESHOOT_DIAGNOSE

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        category = ctx.troubleshoot_issue or "other"
        summary = ctx.extra.get("troubleshoot_summary", "")

        prompt = PROMPT_PROCESS_TROUBLESHOOT_DIAGNOSE.format(
            category=category,
            summary=summary,
            user_message=user_input,
        )
        response = ChatProvider.chat(prompt)

        ctx.extra["troubleshoot_diagnosis"] = response.get("Diagnosis", [])
        ctx.extra["troubleshoot_details"] = user_input

        # Build diagnosis display
        lines = ["## Diagnosis", ""]
        for d in response.get("Diagnosis", []):
            prob = d.get("probability", "unknown")
            cause = d.get("cause", "")
            lines.append(f"- **[{prob.upper()}]** {cause}")

        key_q = response.get("Key_Question", "")
        if key_q:
            lines.extend(["", f"**Key follow-up:** {key_q}"])

        return StepOutput(result=StepResult.CONTINUE, message="\n".join(lines), data=response)


class TroubleshootAdvise(WorkflowStep):
    """Generate prioritized troubleshooting plan using domain knowledge."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        from crisprairs.llm.provider import ChatProvider

        category = ctx.troubleshoot_issue or "other"
        knowledge = TROUBLESHOOT_KNOWLEDGE.get(category, TROUBLESHOOT_KNOWLEDGE["other"])

        prompt = PROMPT_PROCESS_TROUBLESHOOT_ADVISE.format(
            category=category,
            summary=ctx.extra.get("troubleshoot_summary", ""),
            details=ctx.extra.get("troubleshoot_details", ""),
            diagnosis=json.dumps(ctx.extra.get("troubleshoot_diagnosis", []), default=str),
            common_causes="\n".join(f"- {c}" for c in knowledge["common_causes"]),
            quick_checks="\n".join(f"- {c}" for c in knowledge["quick_checks"]),
        )
        response = ChatProvider.chat(prompt)

        actions = response.get("Actions", [])
        ctx.troubleshoot_recommendations = [a.get("action", "") for a in actions]

        lines = ["## Troubleshooting Plan", ""]
        for a in actions:
            priority = a.get("priority", "?")
            action = a.get("action", "")
            impact = a.get("expected_impact", "")
            lines.append(f"{priority}. **{action}** (expected impact: {impact})")

        summary = response.get("Summary", "")
        if summary:
            lines.extend(["", f"**Summary:** {summary}"])

        return StepOutput(result=StepResult.DONE, message="\n".join(lines), data=response)
