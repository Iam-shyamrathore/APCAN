"""
Tests for Gemini Service - unit tests with mocked Gemini API.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.gemini_service import GeminiService, HEALTHCARE_SYSTEM_PROMPT, FHIR_TOOLS


pytestmark = pytest.mark.asyncio


class TestGeminiServiceConfig:
    """Tests for Gemini service initialization and configuration."""

    def test_service_lazy_init(self):
        service = GeminiService()
        assert service._configured is False
        assert service._model is None

    @patch("app.services.gemini_service.settings")
    def test_service_raises_without_api_key(self, mock_settings):
        mock_settings.GOOGLE_API_KEY = ""
        service = GeminiService()

        with pytest.raises(RuntimeError, match="GOOGLE_API_KEY is not set"):
            service._ensure_configured()

    @patch("app.services.gemini_service.genai")
    @patch("app.services.gemini_service.settings")
    def test_service_configures_with_api_key(self, mock_settings, mock_genai):
        mock_settings.GOOGLE_API_KEY = "test-api-key-12345"
        mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
        mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048
        mock_settings.GEMINI_TEMPERATURE = 0.7

        service = GeminiService()
        service._ensure_configured()

        mock_genai.configure.assert_called_once_with(api_key="test-api-key-12345")
        mock_genai.GenerativeModel.assert_called_once()
        assert service._configured is True

    def test_system_prompt_contains_healthcare_context(self):
        assert "APCAN" in HEALTHCARE_SYSTEM_PROMPT
        assert "healthcare" in HEALTHCARE_SYSTEM_PROMPT.lower()
        assert "HIPAA" not in HEALTHCARE_SYSTEM_PROMPT or "PHI" in HEALTHCARE_SYSTEM_PROMPT

    def test_fhir_tools_structure(self):
        assert len(FHIR_TOOLS) == 1
        declarations = FHIR_TOOLS[0]["function_declarations"]
        tool_names = [d["name"] for d in declarations]

        assert "search_patients" in tool_names
        assert "get_patient" in tool_names
        assert "get_patient_encounters" in tool_names
        assert "get_patient_appointments" in tool_names
        assert "book_appointment" in tool_names
        assert "cancel_appointment" in tool_names
        assert "get_patient_observations" in tool_names


class TestGeminiServiceChat:
    """Tests for Gemini chat interactions (mocked API)."""

    def _make_service(self):
        with patch("app.services.gemini_service.genai"), patch(
            "app.services.gemini_service.settings"
        ) as mock_settings:
            mock_settings.GOOGLE_API_KEY = "test-key"
            mock_settings.GEMINI_MODEL = "gemini-2.0-flash"
            mock_settings.GEMINI_MAX_OUTPUT_TOKENS = 2048
            mock_settings.GEMINI_TEMPERATURE = 0.7
            service = GeminiService()
            service._ensure_configured()
            return service

    def test_start_chat(self):
        service = self._make_service()
        chat = service.start_chat()
        assert chat is not None

    def test_start_chat_with_history(self):
        service = self._make_service()
        history = [{"role": "user", "parts": ["Hello"]}]
        chat = service.start_chat(history=history)
        assert chat is not None

    async def test_send_message_text_response(self):
        service = self._make_service()

        # Mock chat and response
        mock_chat = MagicMock()
        mock_part = MagicMock()
        mock_part.function_call = None
        mock_part.text = "I can help you with that."

        mock_response = MagicMock()
        mock_response.parts = [mock_part]
        mock_response.usage_metadata = None
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        result = await service.send_message(mock_chat, "Help me")

        assert result["text"] == "I can help you with that."
        assert result["tool_calls"] == []
        assert result["latency_ms"] >= 0

    async def test_send_message_with_tool_call(self):
        service = self._make_service()

        mock_chat = MagicMock()

        # Mock function call part
        mock_fc = MagicMock()
        mock_fc.name = "search_patients"
        mock_fc.args = {"name": "John"}

        mock_part = MagicMock()
        mock_part.function_call = mock_fc
        mock_part.text = None

        mock_response = MagicMock()
        mock_response.parts = [mock_part]
        mock_response.usage_metadata = None
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        result = await service.send_message(mock_chat, "Find patient John")

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "search_patients"
        assert result["tool_calls"][0]["args"]["name"] == "John"

    async def test_send_tool_result(self):
        service = self._make_service()

        mock_chat = MagicMock()

        mock_part = MagicMock()
        mock_part.function_call = None
        mock_part.text = "I found 2 patients named John."

        mock_response = MagicMock()
        mock_response.parts = [mock_part]
        mock_response.usage_metadata = None
        mock_chat.send_message_async = AsyncMock(return_value=mock_response)

        result = await service.send_tool_result(
            mock_chat,
            "search_patients",
            {"success": True, "data": {"total": 2}},
        )

        assert result["text"] == "I found 2 patients named John."
