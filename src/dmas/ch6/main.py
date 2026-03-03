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
        description="Multi-agent research-draft-review workflow pipeline"
    )
    parser.add_argument(
        "--topic",
        default="renewable energy benefits",
        help="Research topic for the pipeline",
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=3,
        help="Maximum revision cycles before accepting (default: 3)",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Hide internal message passing, show only agent output (AutoGen only)",
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

    print_banner(args.framework, "Research-Draft-Review Pipeline")

    if args.framework == Framework.AUTOGEN:
        from dmas.ch6.autogen_backend import run
    elif args.framework == Framework.AGENT_FRAMEWORK:
        from dmas.ch6.agentframework_backend import run
    elif args.framework == Framework.LANGGRAPH:
        from dmas.ch6.langgraph_backend import run

    kwargs = dict(topic=args.topic, model=args.model, max_revisions=args.max_revisions)
    if args.framework == Framework.AUTOGEN:
        kwargs["silent"] = args.silent

    asyncio.run(run(**kwargs))


if __name__ == "__main__":
    cli()
