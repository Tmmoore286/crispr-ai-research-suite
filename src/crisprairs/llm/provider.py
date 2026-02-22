"""LLM provider adapters for OpenAI and Anthropic with shared safeguards."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import dotenv

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


class IdentifiableGeneError(Exception):
    """Raised when prompts contain long contiguous nucleotide sequences."""


@dataclass(frozen=True)
class _ModelRequest:
    request: Any
    use_gpt4: bool = True
    use_gpt4_turbo: bool = False


def _ensure_privacy_safe(payload: Any) -> None:
    from crisprairs.safety.privacy import contains_identifiable_sequences

    if contains_identifiable_sequences(str(payload)):
        raise IdentifiableGeneError(
            "Request may contain identifiable genomic data. "
            "Please remove patient-specific sequences before proceeding."
        )


def _normalize_messages(request: Any) -> list[dict[str, str]]:
    if isinstance(request, list):
        messages: list[dict[str, str]] = []
        for entry in request:
            if isinstance(entry, dict):
                role = str(entry.get("role", "user"))
                content = str(entry.get("content", ""))
            else:
                role = str(getattr(entry, "type", "user"))
                content = str(getattr(entry, "content", entry))
            messages.append({"role": role, "content": content})
        return messages
    return [{"role": "user", "content": str(request)}]


def _parse_json_response(text: str) -> dict:
    from crisprairs.llm.parser import extract_json

    logger.info(text)
    return extract_json(text)


class OpenAIChat:
    """OpenAI chat-completions adapter."""

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            import openai

            cls._client = openai.OpenAI(
                api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY"),
            )
        return cls._client

    @classmethod
    def _model_for(cls, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> str:
        if use_gpt4_turbo:
            return os.getenv("OPENAI_MODEL_TURBO", "gpt-4-turbo")
        if use_gpt4:
            return os.getenv("OPENAI_MODEL", "gpt-4o")
        return "gpt-3.5-turbo"

    @classmethod
    def chat(cls, request, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> dict:
        req = _ModelRequest(
            request=request,
            use_gpt4=use_gpt4,
            use_gpt4_turbo=use_gpt4_turbo,
        )
        _ensure_privacy_safe(req.request)

        messages = _normalize_messages(req.request)
        response = cls._get_client().chat.completions.create(
            model=cls._model_for(req.use_gpt4, req.use_gpt4_turbo),
            messages=messages,
            temperature=0.2,
        )
        text = response.choices[0].message.content
        return _parse_json_response(text)


class AnthropicChat:
    """Anthropic messages API adapter."""

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            import anthropic

            cls._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return cls._client

    @classmethod
    def _model_for(cls, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> str:
        default_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6-20250514")
        if use_gpt4_turbo:
            return os.getenv("ANTHROPIC_MODEL_TURBO", default_model)
        return default_model

    @classmethod
    def chat(cls, request, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> dict:
        req = _ModelRequest(
            request=request,
            use_gpt4=use_gpt4,
            use_gpt4_turbo=use_gpt4_turbo,
        )
        _ensure_privacy_safe(req.request)

        messages = _normalize_messages(req.request)
        system_text = None
        clean_messages: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                clean_messages.append(msg)

        kwargs = {
            "model": cls._model_for(req.use_gpt4, req.use_gpt4_turbo),
            "max_tokens": 4096,
            "messages": clean_messages,
        }
        if system_text:
            kwargs["system"] = system_text

        response = cls._get_client().messages.create(**kwargs)
        text = response.content[0].text
        return _parse_json_response(text)


class ChatProvider:
    """Dispatch layer for provider selection and audit instrumentation."""

    _provider_name = os.getenv("LLM_PROVIDER", "openai").lower().strip()

    @classmethod
    def _backend(cls):
        return AnthropicChat if cls._provider_name == "anthropic" else OpenAIChat

    @classmethod
    def provider_name(cls) -> str:
        return cls._provider_name

    @classmethod
    def model_name(cls) -> str:
        if cls.provider_name() == "anthropic":
            return AnthropicChat._model_for()
        return OpenAIChat._model_for()

    @classmethod
    def chat(cls, request, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> dict:
        backend = cls._backend()
        started = time.time()

        try:
            result = backend.chat(
                request,
                use_gpt4=use_gpt4,
                use_gpt4_turbo=use_gpt4_turbo,
            )
            _log_audit(
                "llm_call",
                provider=cls.provider_name(),
                model=cls.model_name(),
                latency_ms=int((time.time() - started) * 1000),
            )
            return result
        except Exception:
            _log_audit(
                "llm_call_error",
                provider=cls.provider_name(),
                model=cls.model_name(),
                latency_ms=int((time.time() - started) * 1000),
            )
            raise


def _log_audit(event: str, **kwargs) -> None:
    """Best-effort audit logging."""
    try:
        from crisprairs.rpw.audit import AuditLog

        AuditLog.log_event(event, **kwargs)
    except Exception:
        pass
