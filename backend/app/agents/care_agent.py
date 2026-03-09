"""
Care Agent — retrieves and summarises clinical patient data.

Subgraph: understands clinical query → fetches encounters/observations → synthesises answer.
Tools: get_patient, get_patient_encounters, get_patient_observations
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.tools import filter_tools, CARE_TOOLS
from app.core.config import settings

logger = logging.getLogger(__name__)

CARE_SYSTEM_PROMPT = """\
You are the APCAN Care Agent — a knowledgeable healthcare data assistant.

Your responsibilities:
1. Retrieve patient clinical records (encounters, observations, vitals, lab results).
2. Summarise clinical data in plain language suitable for patients and clinicians.
3. Highlight important trends (e.g., rising blood pressure, missed follow-ups).
4. Never diagnose or prescribe — clearly state that clinical decisions require a clinician.

WORKFLOW:
- Confirm which patient's data is needed (use patient context if available).
- Fetch relevant encounters or observations.
- Synthesise findings into a clear, concise summary.
- Flag any concerning values with appropriate caveats.

RULES:
- Never interpret lab results as a diagnosis.
- Always caveat with "Please consult your healthcare provider for medical advice."
- Be concise — responses should be suitable for voice output (2-4 sentences).
- If asked about scheduling or registration, say you'll transfer them.
"""


def should_continue(state: AgentState) -> str:
    """Route: tool calls pending → tools, else → end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_care_graph(all_tools: list) -> StateGraph:
    """
    Build the Care Agent subgraph.

    Args:
        all_tools: Full tool list from build_tools(db).

    Returns:
        Compiled LangGraph StateGraph.
    """
    tools = filter_tools(all_tools, CARE_TOOLS)

    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    ).bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=CARE_SYSTEM_PROMPT)] + list(messages)
        patient_ctx = state.get("patient_context")
        if patient_ctx and patient_ctx.get("id"):
            ctx_msg = (
                f"[Context: Current patient ID={patient_ctx['id']}, "
                f"name={patient_ctx.get('name', 'unknown')}]"
            )
            messages = list(messages) + [SystemMessage(content=ctx_msg)]
        response = await model.ainvoke(messages)
        return {"messages": [response], "current_agent": "care"}

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
