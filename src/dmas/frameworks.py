from __future__ import annotations

from enum import Enum


class Framework(str, Enum):
    AUTOGEN = "autogen"
    AGENT_FRAMEWORK = "agent-framework"
    LANGGRAPH = "langgraph"

    def __str__(self) -> str:
        return self.value


FRAMEWORK_DISPLAY_NAMES: dict[Framework, str] = {
    Framework.AUTOGEN: "AutoGen",
    Framework.AGENT_FRAMEWORK: "Microsoft Agent Framework",
    Framework.LANGGRAPH: "LangGraph",
}


def print_banner(framework: Framework, workflow: str) -> None:
    """Print a banner identifying the active framework and workflow."""
    name = FRAMEWORK_DISPLAY_NAMES[framework]
    print(f"\n[{name}] {workflow}\n")
