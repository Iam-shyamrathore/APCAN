"""
Admin Agent — handles administrative tasks (insurance queries, record lookups, referrals).

Subgraph: classifies admin request → gathers relevant data → provides guidance.
Tools: search_patients, get_patient, get_patient_encounters
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.tools import filter_tools, ADMIN_TOOLS
from app.core.config import settings

logger = logging.getLogger(__name__)

ADMIN_SYSTEM_PROMPT = """\
You are the APCAN Admin Agent — a professional healthcare administration assistant.

Your responsibilities:
1. Help with insurance and billing inquiries.
2. Assist with medical records requests and access.
3. Provide information about referral processes.
4. Look up patient demographics and visit history for administrative purposes.
5. Guide users through common administrative workflows.

RULES:
- Never share insurance or billing details without verifying identity first.
- For complex billing disputes, recommend contacting the billing department directly.
- Be concise — responses should be suitable for voice output (1-3 sentences).
- If asked about clinical data or scheduling, say you'll transfer them.
- Always maintain a professional, helpful tone.
"""


def should_continue(state: AgentState) -> str:
    """Route: tool calls pending → tools, else → end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_admin_graph(all_tools: list) -> StateGraph:
    """
    Build the Admin Agent subgraph.

    Args:
        all_tools: Full tool list from build_tools(db).

    Returns:
        Compiled LangGraph StateGraph.
    """
    tools = filter_tools(all_tools, ADMIN_TOOLS)

    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    ).bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=ADMIN_SYSTEM_PROMPT)] + list(messages)
        patient_ctx = state.get("patient_context")
        if patient_ctx and patient_ctx.get("id"):
            ctx_msg = (
                f"[Context: Current patient ID={patient_ctx['id']}, "
                f"name={patient_ctx.get('name', 'unknown')}]"
            )
            messages = list(messages) + [SystemMessage(content=ctx_msg)]
        response = await model.ainvoke(messages)
        return {"messages": [response], "current_agent": "admin"}

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
