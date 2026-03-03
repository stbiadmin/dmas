from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import (
    ModelClientStreamingChunkEvent,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
)
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from dmas.config import get_api_key
from dmas.ch5.tools import BrowserSession, navigate, click, type_text, scroll, observe_page, screenshot
from dmas.prompts import COMPUTER_USE_AGENT_SYSTEM_MESSAGE


async def run(
    task: str,
    model: str,
    headless: bool = True,
    max_actions: int = 15,
    start_url: str | None = None,
    silent: bool = False,
) -> None:
    """Run the computer use agent using AutoGen."""
    model_client = OpenAIChatCompletionClient(model=model, api_key=get_api_key())
    try:
        async with BrowserSession(headless=headless) as session:
            action_count = 0

            def _check_limit() -> None:
                nonlocal action_count
                action_count += 1
                if action_count > max_actions:
                    raise RuntimeError(
                        f"Action limit reached ({max_actions}). "
                        "Stopping to prevent runaway execution."
                    )

            async def tool_navigate(url: str) -> str:
                """Navigate the browser to a URL.

                Args:
                    url: The URL to navigate to (e.g. "https://example.com").
                """
                _check_limit()
                return await navigate(session, url)

            async def tool_click(selector: str) -> str:
                """Click an element on the page.

                Args:
                    selector: CSS selector for the element to click.
                """
                _check_limit()
                return await click(session, selector)

            async def tool_type_text(selector: str, text: str) -> str:
                """Type text into an input field.

                Args:
                    selector: CSS selector for the input element.
                    text: The text to type.
                """
                _check_limit()
                return await type_text(session, selector, text)

            async def tool_scroll(direction: str, amount: int = 300) -> str:
                """Scroll the page up or down.

                Args:
                    direction: Scroll direction — "up" or "down".
                    amount: Number of pixels to scroll (default 300).
                """
                _check_limit()
                return await scroll(session, direction, amount)

            async def tool_observe_page() -> str:
                """Observe the current page state: title, URL, visible text, and interactive elements."""
                return await observe_page(session)

            async def tool_screenshot() -> str:
                """Take a screenshot of the current page (base64-encoded PNG)."""
                return await screenshot(session)

            tools = [tool_navigate, tool_click, tool_type_text, tool_scroll, tool_observe_page, tool_screenshot]

            agent = AssistantAgent(
                name="browser_agent",
                description="An agent that automates web browsers.",
                system_message=COMPUTER_USE_AGENT_SYSTEM_MESSAGE,
                model_client=model_client,
                tools=tools,
                reflect_on_tool_use=True,
                model_client_stream=True,
                max_tool_iterations=max_actions,
            )

            full_task = task
            if start_url:
                full_task = f"Start by navigating to {start_url}. Then: {task}"

            if silent:
                async for msg in agent.run_stream(task=full_task):
                    if isinstance(msg, ToolCallRequestEvent):
                        for call in msg.content:
                            print(f"  [calling {call.name}...]", flush=True)
                    elif isinstance(msg, ModelClientStreamingChunkEvent):
                        print(msg.content, end="", flush=True)
                print()
            else:
                await Console(agent.run_stream(task=full_task))
    finally:
        await model_client.close()
