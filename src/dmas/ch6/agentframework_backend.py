from __future__ import annotations

import re

from agent_framework import Agent, AgentResponseUpdate
from agent_framework.openai import OpenAIChatClient

from dmas.config import get_api_key
from dmas.prompts import RESEARCHER_SYSTEM_MESSAGE, WRITER_SYSTEM_MESSAGE, REVIEWER_SYSTEM_MESSAGE


def _parse_score(text: str) -> int:
    """Extract the SCORE: N value from reviewer output. Returns 0 on failure."""
    match = re.search(r"SCORE:\s*(\d+)", text)
    return int(match.group(1)) if match else 0


async def _stream_and_collect(agent: Agent, message: str, session) -> str:
    """Stream agent response and return the collected full text."""
    stream = agent.run(message, stream=True, session=session)
    collected = []
    async for update in stream:
        if isinstance(update, AgentResponseUpdate):
            for content in update.contents or []:
                if content.type == "text" and content.text:
                    print(content.text, end="", flush=True)
                    collected.append(content.text)
    await stream.get_final_response()
    print()
    return "".join(collected)


async def run(topic: str, model: str, max_revisions: int = 3) -> None:
    """Run the research-draft-review pipeline using Microsoft Agent Framework."""
    client = OpenAIChatClient(model_id=model, api_key=get_api_key())

    researcher = Agent(
        client,
        instructions=RESEARCHER_SYSTEM_MESSAGE,
        name="researcher",
        description="A thorough research analyst.",
    )
    writer = Agent(
        client,
        instructions=WRITER_SYSTEM_MESSAGE,
        name="writer",
        description="A skilled report writer.",
    )
    reviewer = Agent(
        client,
        instructions=REVIEWER_SYSTEM_MESSAGE,
        name="reviewer",
        description="A critical report reviewer.",
    )

    # Step 1: Research
    print(f"\n{'='*60}")
    print("  [researcher] Gathering research notes...")
    print(f"{'='*60}\n")
    researcher_session = researcher.create_session()
    research_notes = await _stream_and_collect(
        researcher,
        f"Research the following topic thoroughly: {topic}",
        researcher_session,
    )

    # Step 2: Initial draft
    print(f"\n{'='*60}")
    print("  [writer] Writing initial draft...")
    print(f"{'='*60}\n")
    writer_session = writer.create_session()
    draft = await _stream_and_collect(
        writer,
        f"Write a report based on these research notes:\n\n{research_notes}",
        writer_session,
    )

    # Step 3: Review loop
    for revision in range(max_revisions + 1):
        print(f"\n{'='*60}")
        print(f"  [reviewer] Reviewing draft (round {revision + 1})...")
        print(f"{'='*60}\n")
        # Fresh session each review to avoid bias from prior rounds
        reviewer_session = reviewer.create_session()
        review_text = await _stream_and_collect(
            reviewer,
            f"Review this report:\n\n{draft}",
            reviewer_session,
        )
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
            # Reuse writer session so it has revision history
            draft = await _stream_and_collect(
                writer,
                (
                    f"Revise this report based on the reviewer's feedback.\n\n"
                    f"Current draft:\n{draft}\n\n"
                    f"Reviewer feedback:\n{review_text}"
                ),
                writer_session,
            )
        else:
            print(f"  >> Max revisions reached — accepting current draft")
