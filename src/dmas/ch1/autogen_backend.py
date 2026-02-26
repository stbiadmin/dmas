from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dmas.config import get_api_key
from dmas.prompts import CRITIC_SYSTEM_MESSAGE, POET_SYSTEM_MESSAGE


async def run(topic: str, model: str) -> None:
    """Run the haiku poet/critic collaboration using AutoGen."""
    model_client = OpenAIChatCompletionClient(model=model, api_key=get_api_key())
    try:
        poet = AssistantAgent(
            name="poet",
            description="A haiku poet who crafts and revises haikus.",
            system_message=POET_SYSTEM_MESSAGE,
            model_client=model_client,
            model_client_stream=True,
        )
        critic = AssistantAgent(
            name="critic",
            description="A poetry critic who reviews haikus.",
            system_message=CRITIC_SYSTEM_MESSAGE,
            model_client=model_client,
            model_client_stream=True,
        )
        termination = MaxMessageTermination(12) | TextMentionTermination("APPROVE")
        team = RoundRobinGroupChat(
            participants=[poet, critic],
            termination_condition=termination,
        )
        await Console(team.run_stream(task=f"Write a haiku about: {topic}"))
    finally:
        await model_client.close()
