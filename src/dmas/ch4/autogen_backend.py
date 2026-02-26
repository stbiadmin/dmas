from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import ListMemory
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dmas.config import get_api_key
from dmas.ch4.tools import calculate, get_weather
from dmas.prompts import WEATHER_AGENT_SYSTEM_MESSAGE


def _create_agent(
    model_client: OpenAIChatCompletionClient,
    memory: ListMemory | None = None,
) -> AssistantAgent:
    """Create an assistant agent with weather and math tools."""
    kwargs: dict = dict(
        name="assistant",
        description="A helpful assistant with weather and math tools.",
        system_message=WEATHER_AGENT_SYSTEM_MESSAGE,
        model_client=model_client,
        tools=[get_weather, calculate],
        reflect_on_tool_use=True,
        model_client_stream=True,
    )
    if memory is not None:
        kwargs["memory"] = [memory]
    return AssistantAgent(**kwargs)


async def run_single(city: str, model: str) -> None:
    """Single-turn: ask for weather in one city."""
    model_client = OpenAIChatCompletionClient(model=model, api_key=get_api_key())
    try:
        agent = _create_agent(model_client)
        await Console(agent.run_stream(task=f"What's the weather in {city}?"))
    finally:
        await model_client.close()


async def run_multi_turn(turns: list[str], model: str) -> None:
    """Multi-turn conversation with memory persistence across calls."""
    model_client = OpenAIChatCompletionClient(model=model, api_key=get_api_key())
    try:
        memory = ListMemory()
        agent = _create_agent(model_client, memory=memory)

        for i, task in enumerate(turns, 1):
            print(f"\n{'='*60}")
            print(f"  Turn {i}: {task}")
            print(f"{'='*60}\n")
            await Console(agent.run_stream(task=task))

        if memory.content:
            print(f"\n{'='*60}")
            print("  Memory contents after conversation:")
            print(f"{'='*60}")
            for item in memory.content:
                text = item.content if isinstance(item.content, str) else str(item.content)
                print(f"  - {text[:120]}")
    finally:
        await model_client.close()
