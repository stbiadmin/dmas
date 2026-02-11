from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_core.memory import ListMemory
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dmas.ch4.tools import calculate, get_weather


def create_weather_agent(
    model_client: OpenAIChatCompletionClient,
    memory: ListMemory | None = None,
) -> AssistantAgent:
    """Create a full-featured assistant agent with tools, memory, and streaming.

    Tools:
        - get_weather: look up live weather via wttr.in
        - calculate: evaluate math expressions

    Features:
        - reflect_on_tool_use: agent summarises tool results in natural language
        - model_client_stream: token-level streaming for real-time output
        - memory: ListMemory for multi-turn conversation context
    """
    kwargs: dict = dict(
        name="assistant",
        description="A helpful assistant with weather and math tools.",
        system_message=(
            "You are a helpful assistant. You have access to tools for "
            "checking the weather and evaluating math expressions. Use them "
            "when appropriate. Remember what the user tells you across turns "
            "and refer back to earlier context when relevant."
        ),
        model_client=model_client,
        tools=[get_weather, calculate],
        reflect_on_tool_use=True,
        model_client_stream=True,
    )
    if memory is not None:
        kwargs["memory"] = [memory]
    return AssistantAgent(**kwargs)
