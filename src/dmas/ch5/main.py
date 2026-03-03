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
    parser = argparse.ArgumentParser(
        description="Computer use agent with browser automation"
    )
    parser.add_argument(
        "--task",
        default="Go to Hacker News (https://news.ycombinator.com) and list the top 5 stories with their titles and scores.",
        help="Task for the browser agent to perform",
    )
    parser.add_argument("--url", default=None, help="Optional start URL to navigate to first")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode (default)")
    parser.add_argument("--no-headless", action="store_true", help="Run browser with visible UI")
    parser.add_argument("--max-actions", type=int, default=15, help="Maximum browser actions before stopping")
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Hide tool call details, show only agent reasoning and final output (AutoGen only)",
    )
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model to use")
    parser.add_argument(
        "--framework",
        type=Framework,
        default=Framework.AUTOGEN,
        choices=list(Framework),
        help="Agent framework to use (default: autogen)",
    )
    args = parser.parse_args()

    headless = not args.no_headless

    print_banner(args.framework, "Computer Use Agent")

    if args.framework == Framework.AUTOGEN:
        from dmas.ch5.autogen_backend import run
    elif args.framework == Framework.AGENT_FRAMEWORK:
        from dmas.ch5.agentframework_backend import run
    elif args.framework == Framework.LANGGRAPH:
        from dmas.ch5.langgraph_backend import run

    kwargs = dict(
        task=args.task,
        model=args.model,
        headless=headless,
        max_actions=args.max_actions,
        start_url=args.url,
    )
    if args.framework == Framework.AUTOGEN:
        kwargs["silent"] = args.silent

    asyncio.run(run(**kwargs))


if __name__ == "__main__":
    cli()
