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

from dmas.ch4.tools import get_location
from dmas.frameworks import Framework, print_banner


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
    parser.add_argument(
        "--framework",
        type=Framework,
        default=Framework.AUTOGEN,
        choices=list(Framework),
        help="Agent framework to use (default: autogen)",
    )
    args = parser.parse_args()

    if args.framework == Framework.AUTOGEN:
        from dmas.ch4.autogen_backend import run_single, run_multi_turn
    elif args.framework == Framework.AGENT_FRAMEWORK:
        from dmas.ch4.agentframework_backend import run_single, run_multi_turn
    elif args.framework == Framework.LANGGRAPH:
        from dmas.ch4.langgraph_backend import run_single, run_multi_turn

    if args.multi_turn:
        print_banner(args.framework, "Weather & Math Agent (multi-turn)")
        city = get_location()
        turns = [
            f"My name is Alice and I live in {city}.",
            "What's the weather where I live?",
            "What is 15 * 24 + 7?",
        ]
        asyncio.run(run_multi_turn(turns=turns, model=args.model))
    else:
        city = args.city
        if city is None:
            city = get_location()
            print(f"No city specified — picked: {city}")
        print_banner(args.framework, "Weather & Math Agent (single-turn)")
        asyncio.run(run_single(city=city, model=args.model))


if __name__ == "__main__":
    cli()
