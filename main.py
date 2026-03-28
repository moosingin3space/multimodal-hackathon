from typing import TypedDict

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from gradient_adk import entrypoint

load_dotenv()
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from backend.llm import make_llm
from tools.example_tool import get_current_time

# ---------------------------------------------------------------------------
# Model setup
# ---------------------------------------------------------------------------
llm = make_llm()

tools = [get_current_time]
llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------
class State(TypedDict):
    messages: list[HumanMessage | AIMessage]


async def agent_node(state: State) -> State:
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": state["messages"] + [response]}


graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

workflow = graph.compile()


# ---------------------------------------------------------------------------
# Entrypoint — every Gradient ADK agent must expose exactly one @entrypoint
# ---------------------------------------------------------------------------
@entrypoint
async def main(input: dict, context: dict):  # noqa: A002
    result = await workflow.ainvoke(
        {"messages": [HumanMessage(content=input["prompt"])]}
    )
    return {"response": result["messages"][-1].content}


# ---------------------------------------------------------------------------
# CORS — allow browser requests from the local frontend dev server.
# @entrypoint injects `fastapi_app` into this module's globals at decoration
# time (via sys._getframe), so it is available here at module load.
# ---------------------------------------------------------------------------
fastapi_app.add_middleware(  # noqa: F821  # injected by @entrypoint above
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        os.environ.get("FRONTEND_URL", ""),
    ],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
