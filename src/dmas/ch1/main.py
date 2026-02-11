from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Ensure unbuffered stdout so streaming chunks display in real time,
# even when running under `conda run` (which pipes stdout).
os.environ["PYTHONUNBUFFERED"] = "1"
if not sys.stdout.isatty():
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]

from autogen_agentchat.ui import Console

from dmas.config import get_model_client
from dmas.ch1.agents import create_poet, create_critic
from dmas.ch1.team import create_haiku_team


async def run(topic: str = "Star Wars and Imperialism", model: str = "gpt-4.1-mini") -> None:
    """Run the haiku poet/critic collaboration and stream output."""
    model_client = get_model_client(model)
    try:
        poet = create_poet(model_client)
        critic = create_critic(model_client)
        team = create_haiku_team(poet, critic)
        stream = team.run_stream(task=f"Write a haiku about: {topic}")
        await Console(stream)
    finally:
        await model_client.close()


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Haiku poet/critic collaboration")
    parser.add_argument("--topic", default="Star Wars and Imperialism", help="Haiku topic")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model to use")
    args = parser.parse_args()
    asyncio.run(run(topic=args.topic, model=args.model))


if __name__ == "__main__":
    cli()
