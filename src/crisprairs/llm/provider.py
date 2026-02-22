"""LLM provider abstraction: routes calls to OpenAI or Anthropic.

Adapted from our original rpw/providers.py. Drops langchain dependency;
uses openai and anthropic SDKs directly.
"""

from __future__ import annotations

import json
import logging
import os
import time

import dotenv

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


class IdentifiableGeneError(Exception):
    """Raised when a request contains potentially identifiable genomic data."""


class OpenAIChat:
    """OpenAI backend using the openai SDK directly."""

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
        """Send a chat request and parse JSON response.

        Args:
            request: Either a string prompt or a list of message dicts/objects.
            use_gpt4: Use GPT-4 class model.
            use_gpt4_turbo: Use GPT-4 Turbo model.

        Returns:
            Parsed JSON dict from the LLM response.
        """
        from crisprairs.safety.privacy import contains_identifiable_sequences

        if contains_identifiable_sequences(str(request)):
            raise IdentifiableGeneError(
                "Request may contain identifiable genomic data. "
                "Please remove patient-specific sequences before proceeding."
            )

        client = cls._get_client()
        model = cls._model_for(use_gpt4=use_gpt4, use_gpt4_turbo=use_gpt4_turbo)

        if isinstance(request, list):
            messages = []
            for msg in request:
                if isinstance(msg, dict):
                    messages.append(msg)
                else:
                    role = getattr(msg, "type", "user")
                    content = getattr(msg, "content", str(msg))
                    messages.append({"role": role, "content": content})
        else:
            messages = [{"role": "user", "content": str(request)}]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )

        text = response.choices[0].message.content
        logger.info(text)

        from crisprairs.llm.parser import extract_json
        return extract_json(text)


class AnthropicChat:
    """Anthropic Claude backend."""

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            import anthropic

            cls._client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        return cls._client

    @classmethod
    def _model_for(cls, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> str:
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6-20250514")
        if use_gpt4_turbo:
            return os.getenv("ANTHROPIC_MODEL_TURBO", model)
        return model

    @classmethod
    def chat(cls, request, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> dict:
        """Send a chat request and parse JSON response.

        Args:
            request: Either a string prompt or a list of message dicts/objects.
            use_gpt4: Use higher-tier model.
            use_gpt4_turbo: Use turbo-tier model.

        Returns:
            Parsed JSON dict from the LLM response.
        """
        from crisprairs.safety.privacy import contains_identifiable_sequences

        if contains_identifiable_sequences(str(request)):
            raise IdentifiableGeneError(
                "Request may contain identifiable genomic data. "
                "Please remove patient-specific sequences before proceeding."
            )

        client = cls._get_client()
        model = cls._model_for(use_gpt4=use_gpt4, use_gpt4_turbo=use_gpt4_turbo)

        if isinstance(request, list):
            messages = []
            system_text = None
            for msg in request:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                else:
                    role = getattr(msg, "type", "user")
                    content = getattr(msg, "content", str(msg))
                if role == "system":
                    system_text = content
                else:
                    messages.append({"role": role, "content": content})
            kwargs = {}
            if system_text:
                kwargs["system"] = system_text
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=messages,
                **kwargs,
            )
        else:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": str(request)}],
            )

        text = response.content[0].text
        logger.info(text)

        from crisprairs.llm.parser import extract_json
        return extract_json(text)


class ChatProvider:
    """Routes LLM calls to the configured backend (OpenAI or Anthropic).

    Set the ``LLM_PROVIDER`` env var to "openai" (default) or "anthropic".
    """

    _provider_name = os.getenv("LLM_PROVIDER", "openai").lower().strip()

    @classmethod
    def _backend(cls):
        if cls._provider_name == "anthropic":
            return AnthropicChat
        return OpenAIChat

    @classmethod
    def provider_name(cls) -> str:
        return cls._provider_name

    @classmethod
    def model_name(cls) -> str:
        if cls._provider_name == "anthropic":
            return AnthropicChat._model_for()
        return OpenAIChat._model_for()

    @classmethod
    def chat(cls, request, use_gpt4: bool = True, use_gpt4_turbo: bool = False) -> dict:
        """Send a chat request through the configured provider.

        Also logs to the audit trail if available.
        """
        backend = cls._backend()
        start = time.time()
        try:
            result = backend.chat(
                request, use_gpt4=use_gpt4, use_gpt4_turbo=use_gpt4_turbo
            )
            latency_ms = int((time.time() - start) * 1000)
            _log_audit(
                "llm_call",
                provider=cls._provider_name,
                model=cls.model_name(),
                latency_ms=latency_ms,
            )
            return result
        except Exception:
            latency_ms = int((time.time() - start) * 1000)
            _log_audit(
                "llm_call_error",
                provider=cls._provider_name,
                model=cls.model_name(),
                latency_ms=latency_ms,
            )
            raise


def _log_audit(event: str, **kwargs) -> None:
    """Best-effort audit logging."""
    try:
        from crisprairs.rpw.audit import AuditLog
        AuditLog.log_event(event, **kwargs)
    except Exception:
        pass
