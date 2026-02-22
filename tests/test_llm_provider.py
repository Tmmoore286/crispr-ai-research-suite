"""Tests for llm/provider.py — LLM provider adapter."""

from unittest.mock import patch, MagicMock
import pytest

from crisprairs.llm.provider import (
    OpenAIChat,
    AnthropicChat,
    ChatProvider,
    IdentifiableGeneError,
)


class TestOpenAIChat:
    def test_chat_parses_json_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"gene": "TP53"}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(OpenAIChat, "_get_client", return_value=mock_client):
            result = OpenAIChat.chat("What gene?")

        assert result == {"gene": "TP53"}

    def test_chat_strips_markdown_fences(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '```json\n{"gene": "BRCA1"}\n```'
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(OpenAIChat, "_get_client", return_value=mock_client):
            result = OpenAIChat.chat("What gene?")

        assert result == {"gene": "BRCA1"}

    def test_chat_rejects_identifiable_sequence(self):
        long_seq = "A" * 60
        with pytest.raises(IdentifiableGeneError):
            OpenAIChat.chat(long_seq)

    def test_model_selection_default(self):
        model = OpenAIChat._model_for(use_gpt4=True)
        assert "gpt-4" in model

    def test_model_selection_turbo(self):
        model = OpenAIChat._model_for(use_gpt4_turbo=True)
        assert "turbo" in model.lower() or "gpt-4" in model


class TestAnthropicChat:
    def test_chat_parses_json_response(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"cas": "SpCas9"}'
        mock_client.messages.create.return_value = mock_response

        with patch.object(AnthropicChat, "_get_client", return_value=mock_client):
            result = AnthropicChat.chat("Which Cas?")

        assert result == {"cas": "SpCas9"}

    def test_chat_handles_message_list(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"result": "ok"}'
        mock_client.messages.create.return_value = mock_response

        messages = [
            {"role": "system", "content": "You are a CRISPR expert."},
            {"role": "user", "content": "Help me design a guide."},
        ]

        with patch.object(AnthropicChat, "_get_client", return_value=mock_client):
            result = AnthropicChat.chat(messages)

        assert result == {"result": "ok"}
        # Verify system was passed separately
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs.get("system") == "You are a CRISPR expert."

    def test_chat_rejects_identifiable_sequence(self):
        long_seq = "A" * 60
        with pytest.raises(IdentifiableGeneError):
            AnthropicChat.chat(long_seq)


class TestChatProvider:
    def test_provider_name_default(self):
        name = ChatProvider.provider_name()
        assert name in ("openai", "anthropic")

    def test_chat_routes_to_backend(self):
        mock_result = {"gene": "TP53"}
        with patch.object(ChatProvider, "_backend") as mock_backend_fn:
            mock_backend = MagicMock()
            mock_backend.chat.return_value = mock_result
            mock_backend_fn.return_value = mock_backend

            result = ChatProvider.chat("test request")

        assert result == mock_result

    def test_chat_logs_audit_on_success(self):
        mock_result = {"gene": "TP53"}
        with patch.object(ChatProvider, "_backend") as mock_backend_fn:
            mock_backend = MagicMock()
            mock_backend.chat.return_value = mock_result
            mock_backend_fn.return_value = mock_backend

            with patch("crisprairs.llm.provider._log_audit") as mock_audit:
                ChatProvider.chat("test")
                mock_audit.assert_called()
                assert mock_audit.call_args[0][0] == "llm_call"

    def test_chat_logs_audit_on_error(self):
        with patch.object(ChatProvider, "_backend") as mock_backend_fn:
            mock_backend = MagicMock()
            mock_backend.chat.side_effect = RuntimeError("API error")
            mock_backend_fn.return_value = mock_backend

            with patch("crisprairs.llm.provider._log_audit") as mock_audit:
                with pytest.raises(RuntimeError):
                    ChatProvider.chat("test")
                mock_audit.assert_called()
                assert mock_audit.call_args[0][0] == "llm_call_error"
