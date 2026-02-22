"""Pipeline runner that orchestrates workflow step execution.

PipelineRunner manages the lifecycle of a pipeline: advancing through steps,
collecting user input when needed, handling branching, and tracking state.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .workflow import StepResult, WorkflowStep, Router

if TYPE_CHECKING:
    from .context import SessionContext
    from .workflow import StepOutput

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Executes an ordered sequence of WorkflowStep instances.

    The runner maintains a cursor into the current step list and advances
    through steps based on their StepOutput results:

    - CONTINUE: immediately execute the next step
    - WAIT_FOR_INPUT: pause and return control to the caller
    - DONE: the pipeline is finished
    - BRANCH: switch to a different modality's step sequence via the Router

    Usage::

        runner = PipelineRunner(router)
        runner.start("knockout", ctx)

        while not runner.is_done:
            if runner.waiting_for_input:
                output = runner.submit_input(ctx, user_text)
            else:
                output = runner.advance(ctx)
    """

    def __init__(self, router: Router) -> None:
        self._router = router
        self._steps: list[WorkflowStep] = []
        self._cursor: int = 0
        self._done: bool = False
        self._waiting: bool = False
        self._current_modality: str = ""

    @property
    def is_done(self) -> bool:
        return self._done

    @property
    def waiting_for_input(self) -> bool:
        return self._waiting

    @property
    def current_step(self) -> WorkflowStep | None:
        if self._done or self._cursor >= len(self._steps):
            return None
        return self._steps[self._cursor]

    @property
    def current_modality(self) -> str:
        return self._current_modality

    @property
    def step_index(self) -> int:
        return self._cursor

    @property
    def total_steps(self) -> int:
        return len(self._steps)

    def start(self, modality: str, ctx: SessionContext) -> StepOutput:
        """Begin a pipeline for the given modality.

        Loads the step sequence from the router and executes the first step
        (or pauses if it needs input).

        Args:
            modality: The workflow modality key (e.g. "knockout").
            ctx: The session context.

        Returns:
            The StepOutput from the first step (or a prompt message if input needed).
        """
        self._steps = self._router.get(modality)
        self._cursor = 0
        self._done = False
        self._waiting = False
        self._current_modality = modality
        ctx.modality = modality

        logger.info("Pipeline started: modality=%s, steps=%d", modality, len(self._steps))
        return self._run_current(ctx)

    def advance(self, ctx: SessionContext) -> StepOutput:
        """Advance to and execute the next step.

        Call this when the runner is not waiting for input and not done.

        Returns:
            StepOutput from the executed step.

        Raises:
            RuntimeError: If the pipeline is done or waiting for input.
        """
        if self._done:
            raise RuntimeError("Pipeline is already done.")
        if self._waiting:
            raise RuntimeError("Pipeline is waiting for user input. Call submit_input().")

        self._cursor += 1
        if self._cursor >= len(self._steps):
            self._done = True
            from .workflow import StepOutput
            return StepOutput(result=StepResult.DONE, message="Pipeline complete.")

        return self._run_current(ctx)

    def submit_input(self, ctx: SessionContext, user_input: str) -> StepOutput:
        """Submit user input for the current step and execute it.

        Args:
            ctx: The session context.
            user_input: Text provided by the user.

        Returns:
            StepOutput from the step after processing input.

        Raises:
            RuntimeError: If the pipeline is not waiting for input.
        """
        if not self._waiting:
            raise RuntimeError("Pipeline is not waiting for input.")

        self._waiting = False
        step = self._steps[self._cursor]
        logger.info("User input received for step: %s", step.name)
        output = step.execute(ctx, user_input=user_input)
        return self._handle_output(ctx, output)

    def _run_current(self, ctx: SessionContext) -> StepOutput:
        """Execute the current step, handling input-needed pauses."""
        step = self._steps[self._cursor]
        logger.info("Executing step %d/%d: %s", self._cursor + 1, len(self._steps), step.name)

        if step.needs_input:
            self._waiting = True
            from .workflow import StepOutput
            return StepOutput(
                result=StepResult.WAIT_FOR_INPUT,
                message=step.prompt_message,
            )

        output = step.execute(ctx)
        return self._handle_output(ctx, output)

    def _handle_output(self, ctx: SessionContext, output: StepOutput) -> StepOutput:
        """Process a step's output and determine next action."""
        if output.result == StepResult.DONE:
            # If this is the last step, the pipeline is done.
            # Otherwise, treat DONE as "this step is finished" and advance.
            if self._cursor >= len(self._steps) - 1:
                self._done = True
                logger.info("Pipeline done.")
                return output
            # Not the last step — auto-advance like CONTINUE
            self._cursor += 1
            return self._run_current(ctx)

        if output.result == StepResult.BRANCH:
            if not output.branch_to:
                raise ValueError("StepOutput with BRANCH result must set branch_to.")
            logger.info("Branching to modality: %s", output.branch_to)
            return self.start(output.branch_to, ctx)

        if output.result == StepResult.WAIT_FOR_INPUT:
            self._waiting = True
            return output

        # CONTINUE — auto-advance
        if output.result == StepResult.CONTINUE:
            self._cursor += 1
            if self._cursor >= len(self._steps):
                self._done = True
                output.result = StepResult.DONE
                return output
            return self._run_current(ctx)

        return output
