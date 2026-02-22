"""Tests for the automation (protocol generation) workflow."""

from crisprairs.engine.context import SessionContext, DeliveryInfo
from crisprairs.engine.workflow import StepResult
from crisprairs.workflows.automation import (
    AutomationStep,
    generate_protocol,
    _render_template,
    PROTOCOL_TEMPLATES,
)


class TestRenderTemplate:
    def test_basic_render(self):
        result = _render_template("cell_culture", cell_type="HEK293T")
        assert result["title"] == "Cell Culture Preparation"
        assert any("HEK293T" in s for s in result["steps"])

    def test_missing_key_fallback(self):
        result = _render_template("cell_culture")
        assert result["title"] == "Cell Culture Preparation"
        # Steps with unresolved {cell_type} still appear (original template)
        assert len(result["steps"]) == 3

    def test_unknown_template(self):
        result = _render_template("nonexistent_template")
        assert result["title"] == "nonexistent_template"
        assert result["steps"] == []


class TestGenerateProtocol:
    def test_basic_protocol(self):
        ctx = SessionContext()
        sections = generate_protocol(ctx)

        # Always includes cell culture and sanger validation
        titles = [s["title"] for s in sections]
        assert "Cell Culture Preparation" in titles
        assert "Sanger Sequencing Validation" in titles

    def test_lipofection_delivery(self):
        ctx = SessionContext(delivery=DeliveryInfo(method="lipofection"))
        sections = generate_protocol(ctx)
        titles = [s["title"] for s in sections]
        assert "Lipofection" in titles

    def test_electroporation_delivery(self):
        ctx = SessionContext(delivery=DeliveryInfo(method="electroporation"))
        sections = generate_protocol(ctx)
        titles = [s["title"] for s in sections]
        assert "Electroporation" in titles

    def test_knockout_adds_t7e1(self):
        ctx = SessionContext(modality="knockout")
        sections = generate_protocol(ctx)
        titles = [s["title"] for s in sections]
        assert "T7 Endonuclease I Assay" in titles

    def test_non_knockout_skips_t7e1(self):
        ctx = SessionContext(modality="base_editing")
        sections = generate_protocol(ctx)
        titles = [s["title"] for s in sections]
        assert "T7 Endonuclease I Assay" not in titles


class TestAutomationStep:
    def test_generates_protocol(self):
        ctx = SessionContext(
            modality="knockout",
            delivery=DeliveryInfo(method="lipofection"),
        )
        step = AutomationStep()
        out = step.execute(ctx)

        assert out.result == StepResult.DONE
        assert "Automated Protocol" in out.message
        assert out.data["protocol"]

    def test_always_produces_output(self):
        ctx = SessionContext()
        step = AutomationStep()
        out = step.execute(ctx)

        # Even with minimal context, cell culture + sanger are included
        assert out.result == StepResult.DONE
        assert "protocol" in out.data


class TestProtocolTemplates:
    def test_all_templates_have_title_and_steps(self):
        for key, template in PROTOCOL_TEMPLATES.items():
            assert "title" in template, f"Missing title in {key}"
            assert "steps" in template, f"Missing steps in {key}"
            assert len(template["steps"]) > 0, f"Empty steps in {key}"
