"""Tests for engine/runner.py — PipelineRunner."""

import pytest
from crisprairs.engine.workflow import (
    WorkflowStep,
    StepOutput,
    StepResult,
    Router,
)
from crisprairs.engine.context import SessionContext
from crisprairs.engine.runner import PipelineRunner


# -- Test step implementations --

class StepA(WorkflowStep):
    def execute(self, ctx, user_input=None):
        ctx.extra["step_a"] = True
        return StepOutput(result=StepResult.CONTINUE, message="A done")


class StepB(WorkflowStep):
    @property
    def needs_input(self):
        return True

    @property
    def prompt_message(self):
        return "Enter gene:"

    def execute(self, ctx, user_input=None):
        ctx.target_gene = user_input or ""
        return StepOutput(result=StepResult.CONTINUE, message=f"Gene: {ctx.target_gene}")


class StepC(WorkflowStep):
    def execute(self, ctx, user_input=None):
        ctx.extra["step_c"] = True
        return StepOutput(result=StepResult.DONE, message="All done")


class StepBranch(WorkflowStep):
    def execute(self, ctx, user_input=None):
        return StepOutput(
            result=StepResult.BRANCH,
            message="Branching",
            branch_to="alternate",
        )


class StepAlt(WorkflowStep):
    def execute(self, ctx, user_input=None):
        ctx.extra["alt"] = True
        return StepOutput(result=StepResult.DONE, message="Alt done")


# -- Tests --

class TestPipelineRunnerBasic:
    def _make_runner(self):
        router = Router()
        router.register("test", [StepA(), StepB(), StepC()])
        return PipelineRunner(router)

    def test_start_runs_auto_step(self):
        runner = self._make_runner()
        ctx = SessionContext()
        output = runner.start("test", ctx)
        # StepA is auto → continues to StepB which needs input
        assert runner.waiting_for_input is True
        assert "Enter gene" in output.message

    def test_submit_input(self):
        runner = self._make_runner()
        ctx = SessionContext()
        runner.start("test", ctx)
        assert runner.waiting_for_input

        output = runner.submit_input(ctx, "TP53")
        assert ctx.target_gene == "TP53"
        # After StepB (CONTINUE) → StepC (DONE)
        assert runner.is_done is True

    def test_full_pipeline_flow(self):
        runner = self._make_runner()
        ctx = SessionContext()

        runner.start("test", ctx)
        assert ctx.extra.get("step_a") is True  # StepA ran
        assert runner.waiting_for_input is True

        output = runner.submit_input(ctx, "BRCA1")
        assert ctx.target_gene == "BRCA1"
        assert ctx.extra.get("step_c") is True  # StepC ran
        assert runner.is_done is True

    def test_modality_set_on_context(self):
        runner = self._make_runner()
        ctx = SessionContext()
        runner.start("test", ctx)
        assert ctx.modality == "test"


class TestPipelineRunnerProperties:
    def test_current_step(self):
        router = Router()
        steps = [StepA(), StepB()]
        router.register("test", steps)
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("test", ctx)
        # StepA auto-continued, now at StepB (waiting)
        assert runner.current_step is steps[1]

    def test_total_steps(self):
        router = Router()
        router.register("test", [StepA(), StepC()])
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("test", ctx)
        assert runner.total_steps == 2

    def test_current_modality(self):
        router = Router()
        router.register("knockout", [StepC()])
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("knockout", ctx)
        assert runner.current_modality == "knockout"

    def test_current_step_none_when_done(self):
        router = Router()
        router.register("test", [StepC()])
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("test", ctx)
        assert runner.is_done
        assert runner.current_step is None


class TestPipelineRunnerBranching:
    def test_branch_switches_modality(self):
        router = Router()
        router.register("main", [StepBranch()])
        router.register("alternate", [StepAlt()])
        runner = PipelineRunner(router)
        ctx = SessionContext()

        output = runner.start("main", ctx)
        assert runner.is_done is True
        assert ctx.extra.get("alt") is True
        assert runner.current_modality == "alternate"


class TestPipelineRunnerErrors:
    def test_advance_when_done_raises(self):
        router = Router()
        router.register("test", [StepC()])
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("test", ctx)
        assert runner.is_done

        with pytest.raises(RuntimeError, match="already done"):
            runner.advance(ctx)

    def test_advance_when_waiting_raises(self):
        router = Router()
        router.register("test", [StepB()])
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("test", ctx)
        assert runner.waiting_for_input

        with pytest.raises(RuntimeError, match="waiting for user input"):
            runner.advance(ctx)

    def test_submit_input_when_not_waiting_raises(self):
        router = Router()
        router.register("test", [StepA(), StepC()])
        runner = PipelineRunner(router)
        ctx = SessionContext()
        runner.start("test", ctx)
        # StepA auto-continues to StepC (DONE) — not waiting

        with pytest.raises(RuntimeError, match="not waiting"):
            runner.submit_input(ctx, "something")

    def test_unknown_modality_raises(self):
        router = Router()
        runner = PipelineRunner(router)
        ctx = SessionContext()
        with pytest.raises(KeyError):
            runner.start("nonexistent", ctx)


class TestPipelineRunnerAllAutoSteps:
    def test_all_auto_steps_run_to_completion(self):
        """Pipeline with only auto-CONTINUE steps should auto-advance to end."""
        router = Router()
        router.register("test", [StepA(), StepA(), StepA()])
        runner = PipelineRunner(router)
        ctx = SessionContext()

        output = runner.start("test", ctx)
        assert runner.is_done is True
        assert ctx.extra.get("step_a") is True
