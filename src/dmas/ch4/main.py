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
from autogen_core.memory import ListMemory

from dmas.config import get_model_client
from dmas.ch4.agents import create_weather_agent
from dmas.ch4.tools import get_location


async def run_single(city: str | None = None, model: str = "gpt-4.1-mini") -> None:
    """Single-turn: ask for weather in one city."""
    if city is None:
        city = get_location()
        print(f"No city specified — picked: {city}\n")

    model_client = get_model_client(model)
    try:
        memory = ListMemory()
        agent = create_weather_agent(model_client, memory=memory)
        stream = agent.run_stream(task=f"What's the weather in {city}?")
        await Console(stream)
    finally:
        await model_client.close()


async def run_multi_turn(model: str = "gpt-4.1-mini") -> None:
    """Multi-turn conversation demonstrating memory persistence across calls.

    Runs three turns:
      1. User introduces themselves and states where they live.
      2. User asks about the weather "where I live" — agent must recall the city.
      3. User asks a math question — agent uses the calculate tool.
    """
    city = get_location()
    turns = [
        f"My name is Alice and I live in {city}.",
        "What's the weather where I live?",
        "What is 15 * 24 + 7?",
    ]

    model_client = get_model_client(model)
    try:
        memory = ListMemory()
        agent = create_weather_agent(model_client, memory=memory)

        for i, task in enumerate(turns, 1):
            print(f"\n{'='*60}")
            print(f"  Turn {i}: {task}")
            print(f"{'='*60}\n")
            stream = agent.run_stream(task=task)
            await Console(stream)

        # Show what memory retained
        if memory.content:
            print(f"\n{'='*60}")
            print("  Memory contents after conversation:")
            print(f"{'='*60}")
            for item in memory.content:
                text = item.content if isinstance(item.content, str) else str(item.content)
                print(f"  - {text[:120]}")
    finally:
        await model_client.close()


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Weather & math agent with tools, memory, and streaming"
    )
    parser.add_argument("--city", default=None, help="City to check weather for")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model to use")
    parser.add_argument(
        "--multi-turn",
        action="store_true",
        help="Run a multi-turn conversation demonstrating memory persistence",
    )
    args = parser.parse_args()

    if args.multi_turn:
        asyncio.run(run_multi_turn(model=args.model))
    else:
        asyncio.run(run_single(city=args.city, model=args.model))


if __name__ == "__main__":
    cli()
