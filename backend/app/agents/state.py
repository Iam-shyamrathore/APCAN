"""
Agent State Definitions — shared TypedDict and enums for all LangGraph agents.

Every agent subgraph and the orchestrator operate on the same AgentState,
ensuring seamless context passing during agent handoffs.
"""

from enum import Enum
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class IntentCategory(str, Enum):
    """High-level intent categories the orchestrator routes to agents."""

    INTAKE = "intake"
    SCHEDULING = "scheduling"
    CARE = "care"
    ADMIN = "admin"
    GENERAL = "general"


class AgentState(TypedDict):
    """
    Shared state threaded through every node in the LangGraph graph.

    Fields:
        messages: Chat history (LangChain BaseMessage list, auto-accumulated).
        current_agent: Which agent subgraph is active (or "orchestrator").
        intent: Classified intent category for routing.
        patient_context: Cached patient info so agents don't re-query.
        session_id: Conversation session ID (links to ConversationSession).
        user_id: Authenticated user ID (from JWT).
        tool_results: Latest tool execution results (cleared each turn).
        metadata: Arbitrary extra data (language, preferences, etc.).
    """

    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: str
    intent: str
    patient_context: dict[str, Any]
    session_id: str
    user_id: int | None
    tool_results: list[dict[str, Any]]
    metadata: dict[str, Any]


def make_initial_state(
    session_id: str,
    user_id: int | None = None,
    patient_context: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AgentState:
    """Create a fresh AgentState for a new conversation turn."""
    return AgentState(
        messages=[],
        current_agent="orchestrator",
        intent=IntentCategory.GENERAL.value,
        patient_context=patient_context or {},
        session_id=session_id,
        user_id=user_id,
        tool_results=[],
        metadata=metadata or {},
    )
