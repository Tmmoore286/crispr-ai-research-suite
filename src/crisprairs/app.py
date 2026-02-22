"""CRISPR AI Research Suite — Gradio chat interface.

Launch with: python -m crisprairs.app
"""

from __future__ import annotations

import logging
import uuid

import gradio as gr

from crisprairs.engine.context import SessionContext
from crisprairs.engine.runner import PipelineRunner
from crisprairs.engine.workflow import Router, StepResult
from crisprairs.rpw.audit import AuditLog
from crisprairs.rpw.feedback import FeedbackCollector
from crisprairs.rpw.protocols import ProtocolGenerator
from crisprairs.rpw.sessions import SessionManager
from crisprairs.safety.biosafety import check_biosafety, format_biosafety_warnings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router setup — register all workflow modalities
# ---------------------------------------------------------------------------

def _build_router() -> Router:
    from crisprairs.workflows.activation_repression import (
        ActRepEntry,
        ActRepGuideDesign,
        ActRepSystemSelect,
        ActRepTarget,
    )
    from crisprairs.workflows.automation import AutomationStep
    from crisprairs.workflows.base_editing import (
        BaseEditingEntry,
        BaseEditingGuideDesign,
        BaseEditingSystemSelect,
        BaseEditingTarget,
    )
    from crisprairs.workflows.delivery import DeliveryEntry, DeliverySelect
    from crisprairs.workflows.knockout import (
        KnockoutGuideDesign,
        KnockoutGuideSelection,
        KnockoutTargetInput,
    )
    from crisprairs.workflows.off_target import (
        OffTargetEntry,
        OffTargetInput,
        OffTargetReport,
        OffTargetScoring,
    )
    from crisprairs.workflows.prime_editing import (
        PrimeEditingEntry,
        PrimeEditingGuideDesign,
        PrimeEditingSystemSelect,
        PrimeEditingTarget,
    )
    from crisprairs.workflows.troubleshoot import (
        TroubleshootAdvise,
        TroubleshootDiagnose,
        TroubleshootEntry,
    )
    from crisprairs.workflows.validation import (
        BlastCheckStep,
        PrimerDesignStep,
        ValidationEntry,
    )

    router = Router()

    router.register("knockout", [
        KnockoutTargetInput(), KnockoutGuideDesign(), KnockoutGuideSelection(),
        DeliveryEntry(), DeliverySelect(),
        ValidationEntry(), PrimerDesignStep(), BlastCheckStep(),
        AutomationStep(),
    ])

    router.register("base_editing", [
        BaseEditingEntry(), BaseEditingSystemSelect(), BaseEditingTarget(),
        BaseEditingGuideDesign(),
        DeliveryEntry(), DeliverySelect(),
        ValidationEntry(), PrimerDesignStep(), BlastCheckStep(),
    ])

    router.register("prime_editing", [
        PrimeEditingEntry(), PrimeEditingSystemSelect(), PrimeEditingTarget(),
        PrimeEditingGuideDesign(),
        DeliveryEntry(), DeliverySelect(),
        ValidationEntry(), PrimerDesignStep(), BlastCheckStep(),
    ])

    router.register("activation", [
        ActRepEntry(), ActRepSystemSelect(), ActRepTarget(), ActRepGuideDesign(),
        DeliveryEntry(), DeliverySelect(),
    ])

    router.register("repression", [
        ActRepEntry(), ActRepSystemSelect(), ActRepTarget(), ActRepGuideDesign(),
        DeliveryEntry(), DeliverySelect(),
    ])

    router.register("off_target", [
        OffTargetEntry(), OffTargetInput(), OffTargetScoring(), OffTargetReport(),
    ])

    router.register("troubleshoot", [
        TroubleshootEntry(), TroubleshootDiagnose(), TroubleshootAdvise(),
    ])

    return router


# ---------------------------------------------------------------------------
# State management helpers
# ---------------------------------------------------------------------------

def _new_session_state():
    """Create fresh session state dict for Gradio."""
    session_id = uuid.uuid4().hex[:12]
    ctx = SessionContext(session_id=session_id)
    AuditLog.set_session(session_id)
    AuditLog.log_event("session_started", session_id=session_id)
    return {
        "session_id": session_id,
        "ctx": ctx,
        "runner": None,
        "started": False,
    }


WELCOME_MESSAGE = """\
**Welcome to CRISPR AI Research Suite**

I can help you design and optimize CRISPR experiments. Choose a workflow to get started:

1. **Knockout** — Gene knockout via guide RNA design
2. **Base Editing** — CBE (C>T) or ABE (A>G) base editing
3. **Prime Editing** — PE2/PE3/PEmax precise editing
4. **Activation** — CRISPRa gene activation
5. **Repression** — CRISPRi gene repression
6. **Off-Target Analysis** — Score and assess guide specificity
7. **Troubleshoot** — Diagnose failed experiments

Type a number or workflow name to begin.
"""

MODALITY_MAP = {
    "1": "knockout",
    "2": "base_editing",
    "3": "prime_editing",
    "4": "activation",
    "5": "repression",
    "6": "off_target",
    "7": "troubleshoot",
    "knockout": "knockout",
    "base editing": "base_editing",
    "base_editing": "base_editing",
    "prime editing": "prime_editing",
    "prime_editing": "prime_editing",
    "activation": "activation",
    "crispra": "activation",
    "repression": "repression",
    "crispri": "repression",
    "off-target": "off_target",
    "off_target": "off_target",
    "troubleshoot": "troubleshoot",
    "troubleshooting": "troubleshoot",
}


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

_router = _build_router()


def chat_respond(message: str, history: list, state: dict | None):
    """Handle a user message and return updated history + state."""
    if state is None:
        state = _new_session_state()

    AuditLog.set_session(state["session_id"])
    ctx = state["ctx"]
    runner = state["runner"]

    # Safety check
    safety_flags = check_biosafety(message)
    if safety_flags:
        warnings = format_biosafety_warnings(safety_flags)
        AuditLog.log_event(
            "safety_block",
            session_id=state["session_id"],
            input_preview=message[:100],
        )
        reply = (
            f"**Safety Notice**\n\n{warnings}\n\n"
            "Please consult your institutional biosafety "
            "committee before proceeding."
        )
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        return history, state

    # If workflow hasn't started, parse modality selection
    if not state["started"]:
        modality = MODALITY_MAP.get(message.strip().lower())
        if modality is None:
            history.append({"role": "user", "content": message})
            history.append({
                "role": "assistant",
                "content": "I didn't recognize that workflow. " + WELCOME_MESSAGE,
            })
            return history, state

        ctx.modality = modality
        runner = PipelineRunner(_router)
        state["runner"] = runner
        state["started"] = True

        output = runner.start(modality, ctx)
        AuditLog.log_event(
            "workflow_started",
            session_id=state["session_id"],
            modality=modality,
        )

        # Collect all auto-advance messages
        messages = [output.message]
        while output.result == StepResult.CONTINUE:
            output = runner.advance(ctx)
            if output.message:
                messages.append(output.message)

        reply = "\n\n".join(m for m in messages if m)

        if output.result == StepResult.WAIT_FOR_INPUT and runner.current_step:
            prompt = runner.current_step.prompt_message
            if prompt:
                reply += f"\n\n---\n\n{prompt}"

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        _save_state(state, history)
        return history, state

    # Workflow is running — submit user input
    if runner is None or runner.is_done:
        history.append({"role": "user", "content": message})
        history.append({
            "role": "assistant",
            "content": "Workflow complete. Start a new session "
            "to begin another experiment.",
        })
        return history, state

    try:
        output = runner.submit_input(ctx, message)
    except Exception as e:
        logger.error("Workflow error: %s", e)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": f"An error occurred: {e}"})
        return history, state

    messages = [output.message]

    # Auto-advance through CONTINUE steps
    while output.result == StepResult.CONTINUE and not runner.is_done:
        try:
            output = runner.advance(ctx)
            if output.message:
                messages.append(output.message)
        except Exception:
            break

    reply = "\n\n".join(m for m in messages if m)

    if output.result == StepResult.WAIT_FOR_INPUT and runner.current_step:
        prompt = runner.current_step.prompt_message
        if prompt:
            reply += f"\n\n---\n\n{prompt}"

    if output.result == StepResult.DONE or runner.is_done:
        reply += (
            "\n\n---\n\n**Workflow complete.** "
            "You can export the protocol or start a new session."
        )
        AuditLog.log_event("workflow_completed", session_id=state["session_id"])

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    _save_state(state, history)
    return history, state


def _save_state(state, history):
    """Persist session state to disk."""
    try:
        ctx = state["ctx"]
        SessionManager.save(
            state["session_id"],
            chat_history=history,
            workflow_state=ctx.modality,
            context_dict=ctx.to_dict(),
        )
    except Exception as e:
        logger.error("Session save error: %s", e)


# ---------------------------------------------------------------------------
# Export handlers
# ---------------------------------------------------------------------------

def export_protocol(state):
    """Generate and return a Markdown protocol."""
    if state is None:
        return "No active session."
    ctx = state["ctx"]
    return ProtocolGenerator.generate(ctx, session_id=state["session_id"])


def export_session(state):
    """Export the full session as Markdown."""
    if state is None:
        return "No active session."
    return SessionManager.export_markdown(state["session_id"])


def new_session(state):
    """Reset to a new session."""
    new_state = _new_session_state()
    return [], new_state, WELCOME_MESSAGE


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def build_app():
    """Build and return the Gradio Blocks app."""
    with gr.Blocks(
        title="CRISPR AI Research Suite",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown("# CRISPR AI Research Suite")
        gr.Markdown(
            "AI-assisted CRISPR experiment design "
            "— from target selection to bench-ready protocols."
        )

        state = gr.State(value=None)

        with gr.Tab("Chat"):
            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": WELCOME_MESSAGE}],
                height=500,
                show_label=False,
            )
            msg = gr.Textbox(
                placeholder="Type your message...",
                show_label=False,
                container=False,
            )
            with gr.Row():
                send_btn = gr.Button("Send", variant="primary")
                new_btn = gr.Button("New Session")

            # Wire up chat
            send_btn.click(
                chat_respond,
                inputs=[msg, chatbot, state],
                outputs=[chatbot, state],
            ).then(lambda: "", outputs=[msg])

            msg.submit(
                chat_respond,
                inputs=[msg, chatbot, state],
                outputs=[chatbot, state],
            ).then(lambda: "", outputs=[msg])

            new_btn.click(
                new_session,
                inputs=[state],
                outputs=[chatbot, state, msg],
            )

            # Feedback
            chatbot.like(FeedbackCollector.on_feedback)

        with gr.Tab("Protocol Export"):
            gr.Markdown("Generate a structured lab protocol from your current session.")
            protocol_btn = gr.Button("Generate Protocol", variant="primary")
            protocol_output = gr.Markdown()
            protocol_btn.click(
                export_protocol,
                inputs=[state],
                outputs=[protocol_output],
            )

        with gr.Tab("Session Export"):
            gr.Markdown("Export the full conversation and session data as Markdown.")
            export_btn = gr.Button("Export Session", variant="primary")
            export_output = gr.Markdown()
            export_btn.click(
                export_session,
                inputs=[state],
                outputs=[export_output],
            )

    return app


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
