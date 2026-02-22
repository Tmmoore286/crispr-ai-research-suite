"""Safe protocol automation — generates executable protocol steps.

This module generates structured protocol commands without using eval()
or any dynamic code execution. Protocols are data-driven: the output
is a list of structured step dicts that can be rendered or exported.
"""

from __future__ import annotations

import logging
from typing import Any

from crisprairs.engine.workflow import WorkflowStep, StepOutput, StepResult
from crisprairs.engine.context import SessionContext

logger = logging.getLogger(__name__)


# Protocol step templates — pure data, no code execution
PROTOCOL_TEMPLATES = {
    "cell_culture": {
        "title": "Cell Culture Preparation",
        "steps": [
            "Thaw and culture {cell_type} cells in recommended medium",
            "Passage cells to 70-80% confluency",
            "Prepare sufficient wells for experiment + controls",
        ],
    },
    "transfection_lipofection": {
        "title": "Lipofection",
        "steps": [
            "Dilute {amount} of DNA/RNP in Opti-MEM",
            "Add {reagent} and mix gently",
            "Incubate 10-15 min at room temperature",
            "Add complex dropwise to cells",
        ],
    },
    "transfection_electroporation": {
        "title": "Electroporation",
        "steps": [
            "Harvest cells and wash with PBS",
            "Resuspend 2e5 cells in nucleofection buffer",
            "Add {amount} of DNA/RNP to cell suspension",
            "Electroporate using {program}",
            "Transfer to pre-warmed medium immediately",
        ],
    },
    "validation_t7e1": {
        "title": "T7 Endonuclease I Assay",
        "steps": [
            "Extract genomic DNA 48-72h post-delivery",
            "PCR amplify target region with validation primers",
            "Denature and re-anneal PCR product (95C 5min, ramp to 25C at 0.1C/s)",
            "Add T7 Endonuclease I, incubate 37C for 30 min",
            "Run on 2% agarose gel and image",
        ],
    },
    "validation_sanger": {
        "title": "Sanger Sequencing Validation",
        "steps": [
            "Extract genomic DNA 48-72h post-delivery",
            "PCR amplify target region",
            "Purify PCR product",
            "Submit for Sanger sequencing",
            "Analyze with ICE (Synthego) or TIDE",
        ],
    },
}


class AutomationStep(WorkflowStep):
    """Generate a structured protocol from the session context."""

    def execute(self, ctx: SessionContext, user_input: str | None = None) -> StepOutput:
        protocol = generate_protocol(ctx)

        if not protocol:
            return StepOutput(
                result=StepResult.DONE,
                message="No protocol steps could be generated from the current session.",
            )

        lines = ["## Automated Protocol", ""]
        for i, section in enumerate(protocol, 1):
            lines.append(f"### {i}. {section['title']}")
            for j, step in enumerate(section["steps"], 1):
                lines.append(f"   {j}. {step}")
            lines.append("")

        return StepOutput(
            result=StepResult.DONE,
            message="\n".join(lines),
            data={"protocol": protocol},
        )


def generate_protocol(ctx: SessionContext) -> list[dict[str, Any]]:
    """Build a protocol from session context using templates.

    Returns a list of protocol section dicts, each with 'title' and 'steps'.
    All step generation is data-driven — no eval() or exec().
    """
    sections = []

    # Cell culture
    sections.append(_render_template("cell_culture", cell_type="target"))

    # Delivery
    method = ctx.delivery.method if ctx.delivery else ""
    if method == "lipofection":
        sections.append(_render_template(
            "transfection_lipofection",
            amount="500 ng plasmid or 10 pmol RNP",
            reagent="Lipofectamine 3000",
        ))
    elif method == "electroporation":
        sections.append(_render_template(
            "transfection_electroporation",
            amount="500 ng plasmid or 10 pmol RNP",
            program="manufacturer-recommended program",
        ))

    # Validation
    modality = ctx.modality or ""
    if "knockout" in modality.lower():
        sections.append(_render_template("validation_t7e1"))
    sections.append(_render_template("validation_sanger"))

    return sections


def _render_template(template_key: str, **kwargs) -> dict[str, Any]:
    """Render a protocol template with variable substitution.

    Uses str.format() for safe string interpolation — no code execution.
    """
    template = PROTOCOL_TEMPLATES.get(template_key, {})
    title = template.get("title", template_key)
    steps = []
    for step_template in template.get("steps", []):
        try:
            steps.append(step_template.format(**kwargs))
        except KeyError:
            steps.append(step_template)
    return {"title": title, "steps": steps}
