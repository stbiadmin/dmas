from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph

from dmas.config import get_api_key
from dmas.prompts import CRITIC_SYSTEM_MESSAGE, POET_SYSTEM_MESSAGE


async def run(topic: str, model: str) -> None:
    """Run the haiku poet/critic collaboration using LangGraph."""
    llm = ChatOpenAI(model=model, api_key=get_api_key(), streaming=True)

    async def poet_node(state: MessagesState) -> dict:
        response = await llm.ainvoke([SystemMessage(content=POET_SYSTEM_MESSAGE)] + state["messages"])
        return {"messages": [response]}

    async def critic_node(state: MessagesState) -> dict:
        response = await llm.ainvoke(
            [SystemMessage(content=CRITIC_SYSTEM_MESSAGE)] + state["messages"]
        )
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        messages = state["messages"]
        if len(messages) >= 12:
            return END
        last = messages[-1]
        if isinstance(last, AIMessage) and "APPROVE" in last.content:
            return END
        return "poet"

    graph = StateGraph(MessagesState)
    graph.add_node("poet", poet_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("poet")
    graph.add_edge("poet", "critic")
    graph.add_conditional_edges("critic", should_continue, {"poet": "poet", END: END})

    app = graph.compile()

    inputs = {"messages": [HumanMessage(content=f"Write a haiku about: {topic}")]}
    current_node = None

    async for msg, metadata in app.astream(inputs, stream_mode="messages"):
        node = metadata.get("langgraph_node", "")
        if node and node != current_node:
            current_node = node
            print(f"\n[{current_node}]")
        if isinstance(msg, AIMessage) and msg.content:
            print(msg.content, end="", flush=True)

    print()
