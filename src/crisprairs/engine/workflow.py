"""Workflow step abstractions for the CRISPR AI pipeline engine.

Defines the WorkflowStep ABC, StepOutput/StepResult types, and the Router
that maps modality names to step sequences.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .context import SessionContext


class StepResult(enum.Enum):
    """Outcome of a workflow step execution."""

    CONTINUE = "continue"          # Advance to the next step automatically
    WAIT_FOR_INPUT = "wait_input"  # Pause and collect user input
    DONE = "done"                  # Workflow sequence is complete
    BRANCH = "branch"              # Switch to a different step sequence


@dataclass
class StepOutput:
    """Value returned by WorkflowStep.execute().

    Attributes:
        result: The step outcome that controls pipeline flow.
        message: Text to display to the user (Markdown OK).
        data: Arbitrary structured data produced by this step.
        branch_to: When result is BRANCH, the modality key to branch to.
    """

    result: StepResult
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    branch_to: str | None = None


class WorkflowStep(ABC):
    """Abstract base for all pipeline steps.

    Subclasses implement ``execute()`` which receives the session context
    and (optionally) user input, and returns a ``StepOutput``.
    """

    @property
    def name(self) -> str:
        """Human-readable step name, defaults to class name."""
        return self.__class__.__name__

    @property
    def needs_input(self) -> bool:
        """If True, the runner will collect user input before calling execute()."""
        return False

    @property
    def prompt_message(self) -> str:
        """Message shown to the user when requesting input.

        Only used when ``needs_input`` is True.
        """
        return ""

    @abstractmethod
    def execute(
        self,
        ctx: SessionContext,
        user_input: str | None = None,
    ) -> StepOutput:
        """Run this step.

        Args:
            ctx: Mutable session context shared across steps.
            user_input: User-provided text (present when needs_input is True).

        Returns:
            StepOutput describing the outcome.
        """
        ...


class Router:
    """Maps modality names to ordered sequences of workflow steps.

    Usage::

        router = Router()
        router.register("knockout", [CasSelectionStep(), GuideDesignStep(), ...])
        steps = router.get("knockout")
    """

    def __init__(self) -> None:
        self._routes: dict[str, list[WorkflowStep]] = {}

    def register(self, modality: str, steps: list[WorkflowStep]) -> None:
        """Register a step sequence for a modality.

        Args:
            modality: Canonical name (e.g. "knockout", "base_editing").
            steps: Ordered list of WorkflowStep instances.
        """
        self._routes[modality.lower()] = steps

    def get(self, modality: str) -> list[WorkflowStep]:
        """Retrieve the step sequence for a modality.

        Args:
            modality: Canonical name.

        Returns:
            List of WorkflowStep instances.

        Raises:
            KeyError: If the modality is not registered.
        """
        key = modality.lower()
        if key not in self._routes:
            raise KeyError(
                f"Unknown modality '{modality}'. "
                f"Available: {', '.join(sorted(self._routes))}"
            )
        return self._routes[key]

    @property
    def modalities(self) -> list[str]:
        """List all registered modality names."""
        return sorted(self._routes.keys())
