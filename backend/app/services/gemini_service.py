"""
Gemini AI Service - Google Gemini 2.0 Flash integration
Handles: chat completions, function calling, streaming responses
"""

import logging
import time
from typing import AsyncGenerator

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.core.config import settings

logger = logging.getLogger(__name__)

# Healthcare system prompt - instructs the AI on role and constraints
HEALTHCARE_SYSTEM_PROMPT = """You are APCAN (Autonomous Patient Care and Administrative Navigator), \
a voice-first healthcare AI assistant. You help patients and clinical staff with:

1. **Patient Intake**: Collect demographics, symptoms, and medical history.
2. **Appointment Scheduling**: Check availability, book, reschedule, or cancel appointments.
3. **Clinical Data Retrieval**: Look up patient records, encounters, observations, and lab results.
4. **Care Navigation**: Answer questions about procedures, medications, and follow-ups.

RULES:
- Always be empathetic, clear, and professional.
- Never diagnose conditions or prescribe medications — defer to clinicians.
- When retrieving patient data, confirm the patient's identity first.
- Protect PHI: never repeat sensitive data unless the user is authenticated.
- If you are unsure, say so and offer to connect with a human agent.
- Keep responses concise and suitable for voice output (1-3 sentences when possible).
- When using tools, explain what you're doing in plain language.
"""

# FHIR tool definitions for Gemini function calling
FHIR_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "search_patients",
                "description": "Search for patients by name, MRN, or demographics. "
                "Use this when the user asks to find or look up a patient.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Patient name (given or family) to search for",
                        },
                        "mrn": {
                            "type": "string",
                            "description": "Medical Record Number",
                        },
                        "birth_date": {
                            "type": "string",
                            "description": "Date of birth in YYYY-MM-DD format",
                        },
                    },
                },
            },
            {
                "name": "get_patient",
                "description": "Get detailed information about a specific patient by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The patient's ID number",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
            {
                "name": "get_patient_encounters",
                "description": "Get a patient's clinical encounters (visits). "
                "Use when asked about visit history or recent appointments.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The patient's ID",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: planned, arrived, in-progress, finished, cancelled",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
            {
                "name": "get_patient_appointments",
                "description": "Get a patient's appointments. "
                "Use when asked about upcoming or past appointments.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The patient's ID",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter: proposed, pending, booked, fulfilled, cancelled",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
            {
                "name": "book_appointment",
                "description": "Book a new appointment for a patient. "
                "Use when the user wants to schedule a visit.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The patient's ID",
                        },
                        "appointment_date": {
                            "type": "string",
                            "description": "Desired date and time in ISO 8601 format",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the appointment",
                        },
                        "service_type": {
                            "type": "string",
                            "description": "Type of service: general, specialist, follow-up, urgent",
                        },
                    },
                    "required": ["patient_id", "appointment_date", "reason"],
                },
            },
            {
                "name": "cancel_appointment",
                "description": "Cancel an existing appointment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {
                            "type": "integer",
                            "description": "The appointment ID to cancel",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for cancellation",
                        },
                    },
                    "required": ["appointment_id"],
                },
            },
            {
                "name": "get_patient_observations",
                "description": "Get a patient's clinical observations (vital signs, lab results). "
                "Use when asked about vitals, test results, or measurements.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {
                            "type": "integer",
                            "description": "The patient's ID",
                        },
                        "code": {
                            "type": "string",
                            "description": "LOINC code to filter (e.g., 8867-4 for heart rate)",
                        },
                    },
                    "required": ["patient_id"],
                },
            },
        ]
    }
]


class GeminiService:
    """
    Manages Gemini 2.0 Flash interactions for the voice AI pipeline.
    Supports: chat, function calling, streaming.
    """

    def __init__(self) -> None:
        self._model: genai.GenerativeModel | None = None
        self._configured = False

    def _ensure_configured(self) -> None:
        """Configure the Gemini client on first use (lazy init)."""
        if self._configured:
            return

        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. "
                "Get a free key at https://aistudio.google.com/app/apikey"
            )

        genai.configure(api_key=api_key)

        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=GenerationConfig(
                max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                temperature=settings.GEMINI_TEMPERATURE,
            ),
            system_instruction=HEALTHCARE_SYSTEM_PROMPT,
            tools=FHIR_TOOLS,
        )
        self._configured = True
        logger.info("Gemini service configured with model=%s", settings.GEMINI_MODEL)

    @property
    def model(self) -> genai.GenerativeModel:
        self._ensure_configured()
        assert self._model is not None
        return self._model

    def start_chat(self, history: list[dict] | None = None) -> genai.ChatSession:
        """
        Start a new chat session, optionally with prior history.

        Args:
            history: List of prior messages in Gemini format
                     [{"role": "user", "parts": ["text"]}, ...]

        Returns:
            A ChatSession that maintains multi-turn context.
        """
        return self.model.start_chat(history=history or [])

    async def send_message(
        self,
        chat: genai.ChatSession,
        message: str,
    ) -> dict:
        """
        Send a message and get a complete response (non-streaming).

        Returns:
            {
                "text": str,
                "tool_calls": [{"name": str, "args": dict}, ...],
                "tokens_used": int | None,
                "latency_ms": int,
            }
        """
        start = time.monotonic()

        response = await chat.send_message_async(message)

        latency_ms = int((time.monotonic() - start) * 1000)

        tool_calls = []
        text_parts = []

        for part in response.parts:
            if part.function_call:
                fc = part.function_call
                tool_calls.append({"name": fc.name, "args": dict(fc.args) if fc.args else {}})
            elif part.text:
                text_parts.append(part.text)

        tokens_used = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_used = getattr(response.usage_metadata, "total_token_count", None)

        return {
            "text": "".join(text_parts),
            "tool_calls": tool_calls,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
        }

    async def send_message_stream(
        self,
        chat: genai.ChatSession,
        message: str,
    ) -> AsyncGenerator[dict, None]:
        """
        Send a message and stream the response chunks.

        Yields:
            {"type": "text", "chunk": str} or
            {"type": "tool_call", "name": str, "args": dict}
        """
        response = await chat.send_message_async(message, stream=True)

        async for chunk in response:
            for part in chunk.parts:
                if part.function_call:
                    fc = part.function_call
                    yield {
                        "type": "tool_call",
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }
                elif part.text:
                    yield {"type": "text", "chunk": part.text}

    async def send_tool_result(
        self,
        chat: genai.ChatSession,
        tool_name: str,
        result: dict,
    ) -> dict:
        """
        Send tool execution results back to the model for follow-up response.

        Args:
            chat: Active chat session
            tool_name: Name of the tool that was called
            result: The tool's output data

        Returns:
            Same format as send_message response.
        """
        start = time.monotonic()

        from google.protobuf.struct_pb2 import Struct

        result_struct = Struct()
        result_struct.update(result)

        function_response = genai.protos.Part(
            function_response=genai.protos.FunctionResponse(
                name=tool_name,
                response=result_struct,
            )
        )

        response = await chat.send_message_async(function_response)
        latency_ms = int((time.monotonic() - start) * 1000)

        text_parts = []
        tool_calls = []
        for part in response.parts:
            if part.function_call:
                fc = part.function_call
                tool_calls.append({"name": fc.name, "args": dict(fc.args) if fc.args else {}})
            elif part.text:
                text_parts.append(part.text)

        return {
            "text": "".join(text_parts),
            "tool_calls": tool_calls,
            "tokens_used": None,
            "latency_ms": latency_ms,
        }


# Global singleton
gemini_service = GeminiService()
