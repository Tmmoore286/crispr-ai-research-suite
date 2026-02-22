"""Tests for engine/workflow.py — WorkflowStep, StepOutput, StepResult, Router."""

import pytest
from crisprairs.engine.workflow import (
    WorkflowStep,
    StepOutput,
    StepResult,
    Router,
)
from crisprairs.engine.context import SessionContext


# -- Concrete step implementations for testing --

class AutoStep(WorkflowStep):
    """Step that runs automatically, no input needed."""

    def execute(self, ctx, user_input=None):
        ctx.extra["auto_ran"] = True
        return StepOutput(result=StepResult.CONTINUE, message="Auto step done.")


class InputStep(WorkflowStep):
    """Step that requires user input."""

    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return "Please enter your gene name:"

    def execute(self, ctx, user_input=None):
        ctx.target_gene = user_input or ""
        return StepOutput(
            result=StepResult.CONTINUE,
            message=f"Gene set to {ctx.target_gene}",
        )


class DoneStep(WorkflowStep):
    """Step that signals pipeline completion."""

    def execute(self, ctx, user_input=None):
        return StepOutput(result=StepResult.DONE, message="All done.")


class BranchStep(WorkflowStep):
    """Step that branches to another modality."""

    def execute(self, ctx, user_input=None):
        return StepOutput(
            result=StepResult.BRANCH,
            message="Branching to base_editing.",
            branch_to="base_editing",
        )


# -- Tests --

class TestStepResult:
    def test_enum_values(self):
        assert StepResult.CONTINUE.value == "continue"
        assert StepResult.WAIT_FOR_INPUT.value == "wait_input"
        assert StepResult.DONE.value == "done"
        assert StepResult.BRANCH.value == "branch"


class TestStepOutput:
    def test_defaults(self):
        output = StepOutput(result=StepResult.CONTINUE)
        assert output.message == ""
        assert output.data == {}
        assert output.branch_to is None

    def test_with_data(self):
        output = StepOutput(
            result=StepResult.DONE,
            message="Finished",
            data={"gene": "TP53"},
            branch_to=None,
        )
        assert output.data["gene"] == "TP53"
        assert output.message == "Finished"


class TestWorkflowStep:
    def test_auto_step_defaults(self):
        step = AutoStep()
        assert step.name == "AutoStep"
        assert step.needs_input is False
        assert step.prompt_message == ""

    def test_input_step_properties(self):
        step = InputStep()
        assert step.needs_input is True
        assert "gene" in step.prompt_message.lower()

    def test_auto_step_execute(self):
        ctx = SessionContext()
        output = AutoStep().execute(ctx)
        assert output.result == StepResult.CONTINUE
        assert ctx.extra["auto_ran"] is True

    def test_input_step_execute(self):
        ctx = SessionContext()
        output = InputStep().execute(ctx, user_input="TP53")
        assert ctx.target_gene == "TP53"
        assert output.result == StepResult.CONTINUE

    def test_done_step(self):
        ctx = SessionContext()
        output = DoneStep().execute(ctx)
        assert output.result == StepResult.DONE

    def test_branch_step(self):
        ctx = SessionContext()
        output = BranchStep().execute(ctx)
        assert output.result == StepResult.BRANCH
        assert output.branch_to == "base_editing"


class TestRouter:
    def test_register_and_get(self):
        router = Router()
        steps = [AutoStep(), DoneStep()]
        router.register("knockout", steps)
        assert router.get("knockout") == steps

    def test_case_insensitive(self):
        router = Router()
        router.register("Knockout", [AutoStep()])
        result = router.get("knockout")
        assert len(result) == 1

    def test_unknown_modality_raises(self):
        router = Router()
        with pytest.raises(KeyError, match="Unknown modality"):
            router.get("nonexistent")

    def test_modalities_list(self):
        router = Router()
        router.register("knockout", [AutoStep()])
        router.register("base_editing", [AutoStep()])
        assert router.modalities == ["base_editing", "knockout"]

    def test_error_message_lists_available(self):
        router = Router()
        router.register("knockout", [AutoStep()])
        router.register("prime_editing", [AutoStep()])
        with pytest.raises(KeyError, match="knockout"):
            router.get("nonexistent")
