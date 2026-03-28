"""Agent: discover a company's direct competitors via Exa web search."""
import json
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from backend.llm import make_llm
from backend.tools.exa_tools import exa_search

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
_SYSTEM = """\
You are a market research analyst. Identify the direct competitors of the company \
you are given using web research.

Use the exa_search tool to run 2-4 searches such as:
  - "{company} competitors alternatives"
  - "companies competing with {company}"
  - "{company} vs [likely competitor] comparison"

After searching, respond with a JSON array of competitor company names ranked \
from most-direct to least-direct. Include 5–15 companies.

Rules:
  - Real company names only (not product categories or generic descriptions)
  - Exclude the target company itself
  - Return ONLY a JSON array of strings — no markdown fences, no preamble."""

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
_TOOLS = [exa_search]


class _State(TypedDict):
    messages: Annotated[list, add_messages]


def _build_graph():
    llm = make_llm().bind_tools(_TOOLS)

    async def agent_node(state: _State) -> _State:
        return {"messages": [await llm.ainvoke(state["messages"])]}

    g = StateGraph(_State)
    g.add_node("agent", agent_node)
    g.add_node("tools", ToolNode(_TOOLS))
    g.set_entry_point("agent")
    g.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")
    return g.compile()


_graph = _build_graph()

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run(company: str) -> list[str]:
    """Return a ranked list of competitor names for *company*."""
    result = await _graph.ainvoke(
        {
            "messages": [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=f"Find the competitors of: {company}"),
            ]
        },
        config={"recursion_limit": 10},
    )
    raw = result["messages"][-1].content
    try:
        competitors = json.loads(raw)
        if isinstance(competitors, list):
            return [c for c in competitors if isinstance(c, str) and c.strip()]
    except (json.JSONDecodeError, ValueError):
        pass
    return []
