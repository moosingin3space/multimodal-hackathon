"""Agent: find and rank relevant YouTube videos for a company via yt-dlp search."""
import json
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from backend.llm import make_llm
from backend.tools.youtube_tools import yt_search

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
_SYSTEM = """\
You are a competitive intelligence analyst sourcing YouTube videos about a company.

Use the yt_search tool to run 3-5 targeted searches such as:
  - Product demos, launches, or feature walkthroughs
  - CEO or executive interviews, keynotes, or conference talks
  - Investor presentations or company overviews
  - Third-party reviews or head-to-head comparisons

After searching, respond with a JSON array of the most relevant videos sorted by \
relevancy_score (highest first). Each object must have exactly these keys:
  title           (str)
  url             (str)
  channel         (str)
  views           (int)
  upload_date     (str)
  relevancy_score (float 1–10, how useful for understanding the company)
  reason          (str, one sentence on why this video is relevant)

Return ONLY the JSON array — no markdown fences, no preamble."""

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
_TOOLS = [yt_search]


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
    """Return YouTube videos about *company*, ranked by relevancy.

    Each item: {title, url, channel, views, upload_date, relevancy_score, reason}
    """
    result = await _graph.ainvoke(
        {
            "messages": [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=f"Find relevant YouTube videos for: {company}"),
            ]
        },
        config={"recursion_limit": 14},
    )
    raw = result["messages"][-1].content
    try:
        videos = json.loads(raw)
        if isinstance(videos, list):
            return videos
    except (json.JSONDecodeError, ValueError):
        pass
    return []
