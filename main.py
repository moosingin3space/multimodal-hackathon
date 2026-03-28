import os
from typing import TypedDict

from dotenv import load_dotenv
from gradient_adk import entrypoint

load_dotenv()
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools.example_tool import get_current_time

# ---------------------------------------------------------------------------
# Model setup
# ---------------------------------------------------------------------------
# Uses DigitalOcean Serverless Inference via an OpenAI-compatible endpoint.
# Swap the model name for any model available on Gradient.
llm = ChatOpenAI(
    model="openai-gpt-oss-120b",
    openai_api_base="https://inference.do-ai.run/v1",
    openai_api_key=os.environ["GRADIENT_MODEL_ACCESS_KEY"],
)

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
async def main(input: dict, context: dict):
    result = await workflow.ainvoke(
        {"messages": [HumanMessage(content=input["prompt"])]}
    )
    return {"response": result["messages"][-1].content}
