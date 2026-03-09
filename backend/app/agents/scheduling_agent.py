"""
Scheduling Agent — books, reschedules, and cancels appointments with Calendar sync.

Subgraph: understands request → checks availability → books/cancels in DB + Calendar.
Tools: get_patient_appointments, book_appointment, cancel_appointment,
       check_provider_availability, create_calendar_event, cancel_calendar_event
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.tools import filter_tools, SCHEDULING_TOOLS
from app.core.config import settings

logger = logging.getLogger(__name__)

SCHEDULING_SYSTEM_PROMPT = """\
You are the APCAN Scheduling Agent — an efficient healthcare appointment coordinator.

Your responsibilities:
1. Understand the patient's scheduling request (book, reschedule, or cancel).
2. Check provider availability before confirming a booking.
3. Book the appointment in the system AND create a Google Calendar event.
4. When cancelling, remove both the database record and the Calendar event.
5. Confirm all actions clearly with date, time, and provider details.

WORKFLOW for booking:
- Ask for preferred date/time and reason if not provided.
- Use check_provider_availability to verify the slot is open.
- Use book_appointment to create the DB record.
- Use create_calendar_event to sync to Google Calendar.
- Confirm the booking with all details.

WORKFLOW for cancellation:
- Look up the appointment using get_patient_appointments.
- Use cancel_appointment to update the DB.
- Use cancel_calendar_event to remove the Calendar event (if event ID exists).

RULES:
- Always check availability before booking.
- Default appointment duration is 30 minutes unless specified.
- Be concise — responses should be suitable for voice output (1-3 sentences).
- If the patient asks about medical records or intake, say you'll transfer them.
"""


def should_continue(state: AgentState) -> str:
    """Route: tool calls pending → tools, else → end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_scheduling_graph(all_tools: list) -> StateGraph:
    """
    Build the Scheduling Agent subgraph.

    Args:
        all_tools: Full tool list from build_tools(db).

    Returns:
        Compiled LangGraph StateGraph.
    """
    tools = filter_tools(all_tools, SCHEDULING_TOOLS)

    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    ).bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SCHEDULING_SYSTEM_PROMPT)] + list(messages)
        # Inject patient context if available
        patient_ctx = state.get("patient_context")
        if patient_ctx and patient_ctx.get("id"):
            ctx_msg = (
                f"[Context: Current patient ID={patient_ctx['id']}, "
                f"name={patient_ctx.get('name', 'unknown')}]"
            )
            messages = list(messages) + [SystemMessage(content=ctx_msg)]
        response = await model.ainvoke(messages)
        return {"messages": [response], "current_agent": "scheduling"}

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
