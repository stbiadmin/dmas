from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination


def create_haiku_team(
    poet: AssistantAgent,
    critic: AssistantAgent,
    max_messages: int = 12,
) -> RoundRobinGroupChat:
    """Create a round-robin team that terminates on APPROVE or max messages."""
    termination = MaxMessageTermination(max_messages) | TextMentionTermination("APPROVE")
    return RoundRobinGroupChat(
        participants=[poet, critic],
        termination_condition=termination,
    )
