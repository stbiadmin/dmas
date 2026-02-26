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

from dmas.frameworks import Framework, print_banner


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Haiku poet/critic collaboration")
    parser.add_argument("--topic", default="Star Wars and Imperialism", help="Haiku topic")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model to use")
    parser.add_argument(
        "--framework",
        type=Framework,
        default=Framework.AUTOGEN,
        choices=list(Framework),
        help="Agent framework to use (default: autogen)",
    )
    args = parser.parse_args()

    print_banner(args.framework, "Haiku Poet/Critic Team")

    if args.framework == Framework.AUTOGEN:
        from dmas.ch1.autogen_backend import run
    elif args.framework == Framework.AGENT_FRAMEWORK:
        from dmas.ch1.agentframework_backend import run
    elif args.framework == Framework.LANGGRAPH:
        from dmas.ch1.langgraph_backend import run

    asyncio.run(run(topic=args.topic, model=args.model))


if __name__ == "__main__":
    cli()
