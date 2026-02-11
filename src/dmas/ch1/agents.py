from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


def create_poet(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Create a haiku poet agent."""
    return AssistantAgent(
        name="poet",
        description="A haiku poet who crafts and revises haikus.",
        system_message=(
            "You are a skilled haiku poet. When given a topic, write a haiku "
            "(three lines: 5-7-5 syllables). When you receive feedback from "
            "the critic, revise your haiku accordingly and present the new "
            "version. Always show only the haiku itself, then a brief note "
            "on what you changed (if revising)."
        ),
        model_client=model_client,
        model_client_stream=True,
    )


def create_critic(model_client: OpenAIChatCompletionClient) -> AssistantAgent:
    """Create a poetry critic agent."""
    return AssistantAgent(
        name="critic",
        description="A poetry critic who reviews haikus.",
        system_message=(
            "You are a constructive haiku critic. When you see a haiku, "
            "evaluate its syllable count (5-7-5), imagery, and emotional "
            "impact. Provide 2-3 specific, actionable suggestions for "
            "improvement. Be encouraging but honest.\n\n"
            "When the haiku meets high standards — correct syllable count, "
            "vivid imagery, and emotional resonance — respond with the word "
            "APPROVE on its own line, followed by a brief note of praise."
        ),
        model_client=model_client,
        model_client_stream=True,
    )
