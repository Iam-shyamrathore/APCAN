"""
Orchestrator — the top-level LangGraph StateGraph that routes user messages
to the correct specialised agent (Intake, Scheduling, Care, Admin, or General).

Flow:
  classify_intent  ──→  run_{agent}  ──→  END
                   └──→  general_response  ──→  END

The orchestrator uses a lightweight Gemini call to classify intent, then
delegates to the matching agent subgraph.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState, IntentCategory
from app.agents.tools import build_tools
from app.agents.intake_agent import build_intake_graph
from app.agents.scheduling_agent import build_scheduling_graph
from app.agents.care_agent import build_care_graph
from app.agents.admin_agent import build_admin_graph
from app.core.config import settings

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM_PROMPT = """\
You are a healthcare intent classifier. Given the user's message, classify it into \
exactly ONE of these categories. Respond with ONLY the category name, nothing else.

Categories:
- intake: New patient registration, identity verification, demographic collection
- scheduling: Booking, rescheduling, or cancelling appointments; checking availability
- care: Medical records, vitals, lab results, clinical encounters, health questions
- admin: Insurance, billing, referrals, records requests, administrative tasks
- general: Greetings, small talk, unclear intent, or anything that doesn't fit above

Respond with a single word: intake, scheduling, care, admin, or general
"""

GENERAL_SYSTEM_PROMPT = """\
You are APCAN (Autonomous Patient Care and Administrative Navigator), \
a voice-first healthcare AI assistant. The user's message doesn't clearly fall into \
a specific workflow, so respond helpfully and offer to help with:
- Patient registration (intake)
- Appointment scheduling
- Medical records and vitals
- Administrative questions (insurance, billing)

Be warm, concise, and professional. Keep responses to 1-3 sentences for voice output.
"""


def _parse_intent(text: str) -> IntentCategory:
    """Parse the classifier model's output into an IntentCategory."""
    cleaned = text.strip().lower().rstrip(".")
    for cat in IntentCategory:
        if cat.value in cleaned:
            return cat
    return IntentCategory.GENERAL


async def _classify_intent(state: AgentState) -> dict:
    """Use a lightweight Gemini call to classify the user's intent."""
    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,  # deterministic classification
        max_output_tokens=20,
    )

    # Extract the last user message
    user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_msg = msg.content
            break

    if not user_msg:
        return {"intent": IntentCategory.GENERAL.value, "current_agent": "orchestrator"}

    response = await model.ainvoke(
        [SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT), HumanMessage(content=user_msg)]
    )
    intent = _parse_intent(response.content)
    logger.info("Intent classified: '%s' → %s", user_msg[:80], intent.value)
    return {"intent": intent.value, "current_agent": "orchestrator"}


def _route_to_agent(state: AgentState) -> str:
    """Conditional edge: route to the agent node matching the classified intent."""
    intent = state.get("intent", IntentCategory.GENERAL.value)
    route_map = {
        IntentCategory.INTAKE.value: "intake",
        IntentCategory.SCHEDULING.value: "scheduling",
        IntentCategory.CARE.value: "care",
        IntentCategory.ADMIN.value: "admin",
        IntentCategory.GENERAL.value: "general",
    }
    return route_map.get(intent, "general")


async def _general_response(state: AgentState) -> dict:
    """Handle general/unclassified messages with a direct Gemini response."""
    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    )
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=GENERAL_SYSTEM_PROMPT)] + list(messages)
    response = await model.ainvoke(messages)
    return {"messages": [response], "current_agent": "general"}


def build_orchestrator(db: AsyncSession) -> Any:
    """
    Build the complete orchestrator graph with all agent subgraphs.

    Args:
        db: AsyncSession for the current request (tools need DB access).

    Returns:
        Compiled LangGraph graph ready for .ainvoke(state).
    """
    all_tools = build_tools(db)

    # Pre-build agent subgraphs
    intake_graph = build_intake_graph(all_tools)
    scheduling_graph = build_scheduling_graph(all_tools)
    care_graph = build_care_graph(all_tools)
    admin_graph = build_admin_graph(all_tools)

    # Wrapper nodes that invoke the compiled subgraphs
    async def run_intake(state: AgentState) -> dict:
        result = await intake_graph.ainvoke(state)
        return {"messages": result["messages"], "current_agent": "intake"}

    async def run_scheduling(state: AgentState) -> dict:
        result = await scheduling_graph.ainvoke(state)
        return {"messages": result["messages"], "current_agent": "scheduling"}

    async def run_care(state: AgentState) -> dict:
        result = await care_graph.ainvoke(state)
        return {"messages": result["messages"], "current_agent": "care"}

    async def run_admin(state: AgentState) -> dict:
        result = await admin_graph.ainvoke(state)
        return {"messages": result["messages"], "current_agent": "admin"}

    # Build the top-level orchestrator graph
    graph = StateGraph(AgentState)

    graph.add_node("classify", _classify_intent)
    graph.add_node("intake", run_intake)
    graph.add_node("scheduling", run_scheduling)
    graph.add_node("care", run_care)
    graph.add_node("admin", run_admin)
    graph.add_node("general", _general_response)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        _route_to_agent,
        {
            "intake": "intake",
            "scheduling": "scheduling",
            "care": "care",
            "admin": "admin",
            "general": "general",
        },
    )

    # All agents end after one turn
    graph.add_edge("intake", END)
    graph.add_edge("scheduling", END)
    graph.add_edge("care", END)
    graph.add_edge("admin", END)
    graph.add_edge("general", END)

    return graph.compile()
