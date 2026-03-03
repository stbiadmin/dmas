from __future__ import annotations

from agent_framework import Agent, AgentResponseUpdate, tool
from agent_framework.openai import OpenAIChatClient

from dmas.config import get_api_key
from dmas.ch5.tools import BrowserSession, navigate, click, type_text, scroll, observe_page, screenshot
from dmas.prompts import COMPUTER_USE_AGENT_SYSTEM_MESSAGE


async def run(
    task: str,
    model: str,
    headless: bool = True,
    max_actions: int = 15,
    start_url: str | None = None,
) -> None:
    """Run the computer use agent using Microsoft Agent Framework."""
    client = OpenAIChatClient(model_id=model, api_key=get_api_key())

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

        @tool(description="Navigate the browser to a URL")
        async def tool_navigate(url: str) -> str:
            """Navigate the browser to a URL.

            Args:
                url: The URL to navigate to (e.g. "https://example.com").
            """
            _check_limit()
            return await navigate(session, url)

        @tool(description="Click an element on the page")
        async def tool_click(selector: str) -> str:
            """Click an element on the page.

            Args:
                selector: CSS selector for the element to click.
            """
            _check_limit()
            return await click(session, selector)

        @tool(description="Type text into an input field")
        async def tool_type_text(selector: str, text: str) -> str:
            """Type text into an input field.

            Args:
                selector: CSS selector for the input element.
                text: The text to type.
            """
            _check_limit()
            return await type_text(session, selector, text)

        @tool(description="Scroll the page up or down")
        async def tool_scroll(direction: str, amount: int = 300) -> str:
            """Scroll the page up or down.

            Args:
                direction: Scroll direction — "up" or "down".
                amount: Number of pixels to scroll (default 300).
            """
            _check_limit()
            return await scroll(session, direction, amount)

        @tool(description="Observe the current page state: title, URL, text, and interactive elements")
        async def tool_observe_page() -> str:
            """Observe the current page state."""
            return await observe_page(session)

        @tool(description="Take a screenshot of the current page (base64-encoded PNG)")
        async def tool_screenshot() -> str:
            """Take a screenshot of the current page."""
            return await screenshot(session)

        tools = [tool_navigate, tool_click, tool_type_text, tool_scroll, tool_observe_page, tool_screenshot]

        agent = Agent(
            client,
            instructions=COMPUTER_USE_AGENT_SYSTEM_MESSAGE,
            name="browser_agent",
            description="An agent that automates web browsers.",
            tools=tools,
        )

        full_task = task
        if start_url:
            full_task = f"Start by navigating to {start_url}. Then: {task}"

        agent_session = agent.create_session()
        stream = agent.run(full_task, stream=True, session=agent_session)
        async for update in stream:
            if isinstance(update, AgentResponseUpdate):
                for content in update.contents or []:
                    if content.type == "function_call" and getattr(content, "name", ""):
                        print(f"  [calling {content.name}...]", flush=True)
                    elif content.type == "text" and content.text:
                        print(content.text, end="", flush=True)
        await stream.get_final_response()
        print()
