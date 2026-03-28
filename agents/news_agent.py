"""Agent: find and rank recent news articles for a company using Exa search."""
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
You are a competitive intelligence analyst. Find recent news that reveals \
strategic trends for the company you are given.

Use the exa_search tool to run 3-5 targeted searches covering:
  - Recent product launches or feature announcements
  - Funding rounds, partnerships, or M&A activity
  - Leadership changes or strategic pivots
  - Competitive positioning or market commentary

After searching, respond with a JSON array of the most relevant articles sorted \
by relevancy_score (highest first). Each object must have exactly these keys:
  title           (str)
  url             (str)
  published_date  (str)
  relevancy_score (float 1–10, how revealing for the company's current direction)
  summary         (str, 1–2 sentences on why this matters)

Return ONLY the JSON array — no markdown fences, no preamble."""

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

async def run(company: str) -> list[dict]:
    """Return news articles about *company*, ranked by relevancy.

    Each item: {title, url, published_date, relevancy_score, summary}
    """
    result = await _graph.ainvoke(
        {
            "messages": [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=f"Find recent strategic news for: {company}"),
            ]
        },
        config={"recursion_limit": 14},
    )
    raw = result["messages"][-1].content
    try:
        articles = json.loads(raw)
        if isinstance(articles, list):
            return articles
    except (json.JSONDecodeError, ValueError):
        pass
    return []
