from __future__ import annotations

from agent_framework import Agent, AgentResponseUpdate, Message
from agent_framework.openai import OpenAIChatClient
from agent_framework_orchestrations import GroupChatBuilder, GroupChatState

from dmas.config import get_api_key
from dmas.prompts import CRITIC_SYSTEM_MESSAGE, POET_SYSTEM_MESSAGE


def _round_robin_selector(state: GroupChatState) -> str:
    """Alternate between poet and critic in round-robin order."""
    participants = list(state.participants.keys())
    return participants[state.current_round % len(participants)]


def _termination_condition(messages: list[Message]) -> bool:
    """Terminate on APPROVE mention or after 12 messages (6 rounds)."""
    if len(messages) >= 12:
        return True
    for msg in messages:
        if "APPROVE" in msg.text:
            return True
    return False


async def run(topic: str, model: str) -> None:
    """Run the haiku poet/critic collaboration using Microsoft Agent Framework."""
    client = OpenAIChatClient(model_id=model, api_key=get_api_key())

    poet = Agent(client, instructions=POET_SYSTEM_MESSAGE, name="poet", description="A haiku poet")
    critic = Agent(
        client, instructions=CRITIC_SYSTEM_MESSAGE, name="critic", description="A poetry critic"
    )

    builder = GroupChatBuilder(
        participants=[poet, critic],
        selection_func=_round_robin_selector,
        termination_condition=_termination_condition,
        max_rounds=12,
        intermediate_outputs=True,
    )
    workflow = builder.build()

    stream = workflow.run(f"Write a haiku about: {topic}", stream=True)
    current_executor = None
    async for event in stream:
        if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
            if event.executor_id and event.executor_id != current_executor:
                current_executor = event.executor_id
                print(f"\n[{current_executor}]")
            text = event.data.text
            if text:
                print(text, end="", flush=True)

    print()
