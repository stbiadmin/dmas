from __future__ import annotations

from agent_framework import Agent, AgentResponseUpdate, AgentSession, InMemoryHistoryProvider, tool
from agent_framework.openai import OpenAIChatClient

from dmas.config import get_api_key
from dmas.ch4 import tools as tool_fns
from dmas.prompts import WEATHER_AGENT_SYSTEM_MESSAGE


@tool(description="Get current weather for a city")
async def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: City name (e.g. "Tokyo" or "Austin, Texas, USA").
    """
    return await tool_fns.get_weather(city)


@tool(description="Evaluate a mathematical expression")
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A math expression to evaluate (e.g. "15 * 24", "sqrt(144)").
    """
    return await tool_fns.calculate(expression)


def _create_agent(model: str, *, with_history: bool = False) -> Agent:
    client = OpenAIChatClient(model_id=model, api_key=get_api_key())
    kwargs: dict = dict(
        instructions=WEATHER_AGENT_SYSTEM_MESSAGE,
        name="assistant",
        description="A helpful assistant with weather and math tools.",
        tools=[get_weather, calculate],
    )
    if with_history:
        kwargs["context_providers"] = [InMemoryHistoryProvider()]
    return Agent(client, **kwargs)


async def _stream_response(agent: Agent, message: str, session: AgentSession) -> None:
    """Send a message and stream the response token-by-token."""
    stream = agent.run(message, stream=True, session=session)
    in_tool_call = False
    async for update in stream:
        if isinstance(update, AgentResponseUpdate):
            for content in update.contents or []:
                if content.type == "function_call" and getattr(content, "name", ""):
                    tool_name = content.name
                    print(f"  [calling {tool_name}...]", flush=True)
                    in_tool_call = True
                elif content.type == "function_result":
                    in_tool_call = False
                elif content.type == "text" and content.text:
                    print(content.text, end="", flush=True)
    # Finalize the stream so history providers store the response
    await stream.get_final_response()
    print()


async def run_single(city: str, model: str) -> None:
    """Single-turn: ask for weather in one city."""
    agent = _create_agent(model)
    session = agent.create_session()
    await _stream_response(agent, f"What's the weather in {city}?", session)


async def run_multi_turn(turns: list[str], model: str) -> None:
    """Multi-turn conversation with session persistence across calls."""
    agent = _create_agent(model, with_history=True)
    session = agent.create_session()

    for i, task in enumerate(turns, 1):
        print(f"\n{'='*60}")
        print(f"  Turn {i}: {task}")
        print(f"{'='*60}\n")
        await _stream_response(agent, task, session)
