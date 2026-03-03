from __future__ import annotations

import re

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import ModelClientStreamingChunkEvent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dmas.config import get_api_key
from dmas.prompts import RESEARCHER_SYSTEM_MESSAGE, WRITER_SYSTEM_MESSAGE, REVIEWER_SYSTEM_MESSAGE


def _parse_score(text: str) -> int:
    """Extract the SCORE: N value from reviewer output. Returns 0 on failure."""
    match = re.search(r"SCORE:\s*(\d+)", text)
    return int(match.group(1)) if match else 0


async def _stream_and_collect(agent, task):
    """Iterate run_stream, print only streaming text, return full collected text."""
    collected = []
    async for msg in agent.run_stream(task=task):
        if isinstance(msg, ModelClientStreamingChunkEvent):
            print(msg.content, end="", flush=True)
            collected.append(msg.content)
    print()
    return "".join(collected)


async def run(topic: str, model: str, max_revisions: int = 3, silent: bool = False) -> None:
    """Run the research-draft-review pipeline using AutoGen."""
    model_client = OpenAIChatCompletionClient(model=model, api_key=get_api_key())
    try:
        researcher = AssistantAgent(
            name="researcher",
            description="A thorough research analyst.",
            system_message=RESEARCHER_SYSTEM_MESSAGE,
            model_client=model_client,
            model_client_stream=True,
        )
        writer = AssistantAgent(
            name="writer",
            description="A skilled report writer.",
            system_message=WRITER_SYSTEM_MESSAGE,
            model_client=model_client,
            model_client_stream=True,
        )
        reviewer = AssistantAgent(
            name="reviewer",
            description="A critical report reviewer.",
            system_message=REVIEWER_SYSTEM_MESSAGE,
            model_client=model_client,
            model_client_stream=True,
        )

        # Step 1: Research
        print(f"\n{'='*60}")
        print("  [researcher] Gathering research notes...")
        print(f"{'='*60}\n")
        if silent:
            research_notes = await _stream_and_collect(
                researcher, f"Research the following topic thoroughly: {topic}"
            )
        else:
            result = await Console(
                researcher.run_stream(task=f"Research the following topic thoroughly: {topic}")
            )
            research_notes = result.messages[-1].content

        # Step 2: Initial draft
        print(f"\n{'='*60}")
        print("  [writer] Writing initial draft...")
        print(f"{'='*60}\n")
        writer_task = f"Write a report based on these research notes:\n\n{research_notes}"
        if silent:
            draft = await _stream_and_collect(writer, writer_task)
        else:
            result = await Console(writer.run_stream(task=writer_task))
            draft = result.messages[-1].content

        # Step 3: Review loop
        for revision in range(max_revisions + 1):
            print(f"\n{'='*60}")
            print(f"  [reviewer] Reviewing draft (round {revision + 1})...")
            print(f"{'='*60}\n")
            reviewer_task = f"Review this report:\n\n{draft}"
            if silent:
                review_text = await _stream_and_collect(reviewer, reviewer_task)
            else:
                result = await Console(reviewer.run_stream(task=reviewer_task))
                review_text = result.messages[-1].content
            score = _parse_score(review_text)

            print(f"\n  >> Score: {score}/10")

            if score >= 8:
                print("  >> Report APPROVED")
                break

            if revision < max_revisions:
                print(f"  >> Revisions needed (attempt {revision + 1}/{max_revisions})")
                print(f"\n{'='*60}")
                print(f"  [writer] Revising draft...")
                print(f"{'='*60}\n")
                revision_task = (
                    f"Revise this report based on the reviewer's feedback.\n\n"
                    f"Current draft:\n{draft}\n\n"
                    f"Reviewer feedback:\n{review_text}"
                )
                if silent:
                    draft = await _stream_and_collect(writer, revision_task)
                else:
                    result = await Console(writer.run_stream(task=revision_task))
                    draft = result.messages[-1].content
            else:
                print(f"  >> Max revisions reached — accepting current draft")
    finally:
        await model_client.close()
