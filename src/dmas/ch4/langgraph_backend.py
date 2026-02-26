from __future__ import annotations

import warnings

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from dmas.config import get_api_key
from dmas.ch4 import tools as tool_fns
from dmas.prompts import WEATHER_AGENT_SYSTEM_MESSAGE

# Suppress the deprecation warning for create_react_agent location
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from langgraph.prebuilt import create_react_agent


@tool
async def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: City name (e.g. "Tokyo" or "Austin, Texas, USA").
    """
    return await tool_fns.get_weather(city)


@tool
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A math expression to evaluate (e.g. "15 * 24", "sqrt(144)").
    """
    return await tool_fns.calculate(expression)


async def _astream_with_tools(agent, inputs, config=None):
    """Stream agent output, printing tool-use indicators."""
    kwargs = {"stream_mode": "messages"}
    args = (inputs, config) if config else (inputs,)
    async for msg, metadata in agent.astream(*args, **kwargs):
        if isinstance(msg, (AIMessage, AIMessageChunk)):
            # Tool call start
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc.get("name"):
                        print(f"  [calling {tc['name']}...]", flush=True)
            # Text content (skip tool-call chunks)
            elif msg.content:
                print(msg.content, end="", flush=True)
    print()


async def run_single(city: str, model: str) -> None:
    """Single-turn: ask for weather in one city."""
    llm = ChatOpenAI(model=model, api_key=get_api_key(), streaming=True)
    agent = create_react_agent(llm, [get_weather, calculate], prompt=WEATHER_AGENT_SYSTEM_MESSAGE)

    inputs = {"messages": [HumanMessage(content=f"What's the weather in {city}?")]}
    await _astream_with_tools(agent, inputs)


async def run_multi_turn(turns: list[str], model: str) -> None:
    """Multi-turn conversation with memory persistence across calls."""
    llm = ChatOpenAI(model=model, api_key=get_api_key(), streaming=True)
    memory = MemorySaver()
    agent = create_react_agent(
        llm,
        [get_weather, calculate],
        prompt=WEATHER_AGENT_SYSTEM_MESSAGE,
        checkpointer=memory,
    )
    config = {"configurable": {"thread_id": "multi-turn-session"}}

    for i, task in enumerate(turns, 1):
        print(f"\n{'='*60}")
        print(f"  Turn {i}: {task}")
        print(f"{'='*60}\n")

        inputs = {"messages": [HumanMessage(content=task)]}
        await _astream_with_tools(agent, inputs, config)
