"""
Intake Agent — handles new patient registration and identity verification.

Subgraph: collects demographics, verifies identity, confirms patient record.
Tools: search_patients, get_patient
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.state import AgentState
from app.agents.tools import filter_tools, INTAKE_TOOLS
from app.core.config import settings

logger = logging.getLogger(__name__)

INTAKE_SYSTEM_PROMPT = """\
You are the APCAN Intake Agent — a friendly, empathetic healthcare receptionist AI.

Your responsibilities:
1. Greet the patient warmly and ask for identifying information (name, date of birth, MRN).
2. Search the system for matching patient records.
3. If found, confirm the patient's identity by verifying details.
4. If not found, let the patient know and offer to connect them with a human agent.
5. Collect any missing demographics (phone, address, insurance) when appropriate.

RULES:
- Never diagnose or give medical advice.
- Protect PHI — only share info after identity is confirmed.
- Be concise — responses should be suitable for voice output (1-3 sentences).
- If the patient asks about scheduling or medical records, say you'll transfer them to the right team.
"""


def should_continue(state: AgentState) -> str:
    """Route after the model node: if tool calls pending → tools, else → end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_intake_graph(all_tools: list) -> StateGraph:
    """
    Build the Intake Agent subgraph.

    Args:
        all_tools: Full tool list from build_tools(db).
                   Will be filtered to intake-only tools.

    Returns:
        Compiled LangGraph StateGraph.
    """
    tools = filter_tools(all_tools, INTAKE_TOOLS)

    model = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    ).bind_tools(tools)

    async def agent_node(state: AgentState) -> dict:
        """Invoke the model with the current messages."""
        messages = state["messages"]
        # Prepend system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=INTAKE_SYSTEM_PROMPT)] + list(messages)
        response = await model.ainvoke(messages)
        return {"messages": [response], "current_agent": "intake"}

    tool_node = ToolNode(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
