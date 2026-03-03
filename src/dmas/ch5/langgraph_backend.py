from __future__ import annotations

import warnings

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from dmas.config import get_api_key
from dmas.ch5.tools import BrowserSession, navigate, click, type_text, scroll, observe_page, screenshot
from dmas.prompts import COMPUTER_USE_AGENT_SYSTEM_MESSAGE

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from langgraph.prebuilt import create_react_agent


async def run(
    task: str,
    model: str,
    headless: bool = True,
    max_actions: int = 15,
    start_url: str | None = None,
) -> None:
    """Run the computer use agent using LangGraph."""
    llm = ChatOpenAI(model=model, api_key=get_api_key(), streaming=True)

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

        @tool
        async def tool_navigate(url: str) -> str:
            """Navigate the browser to a URL.

            Args:
                url: The URL to navigate to (e.g. "https://example.com").
            """
            _check_limit()
            return await navigate(session, url)

        @tool
        async def tool_click(selector: str) -> str:
            """Click an element on the page.

            Args:
                selector: CSS selector for the element to click.
            """
            _check_limit()
            return await click(session, selector)

        @tool
        async def tool_type_text(selector: str, text: str) -> str:
            """Type text into an input field.

            Args:
                selector: CSS selector for the input element.
                text: The text to type.
            """
            _check_limit()
            return await type_text(session, selector, text)

        @tool
        async def tool_scroll(direction: str, amount: int = 300) -> str:
            """Scroll the page up or down.

            Args:
                direction: Scroll direction — "up" or "down".
                amount: Number of pixels to scroll (default 300).
            """
            _check_limit()
            return await scroll(session, direction, amount)

        @tool
        async def tool_observe_page() -> str:
            """Observe the current page state: title, URL, visible text, and interactive elements."""
            return await observe_page(session)

        @tool
        async def tool_screenshot() -> str:
            """Take a screenshot of the current page (base64-encoded PNG)."""
            return await screenshot(session)

        tools = [tool_navigate, tool_click, tool_type_text, tool_scroll, tool_observe_page, tool_screenshot]

        agent = create_react_agent(llm, tools, prompt=COMPUTER_USE_AGENT_SYSTEM_MESSAGE)

        full_task = task
        if start_url:
            full_task = f"Start by navigating to {start_url}. Then: {task}"

        inputs = {"messages": [HumanMessage(content=full_task)]}
        async for msg, metadata in agent.astream(inputs, stream_mode="messages"):
            if isinstance(msg, (AIMessage, AIMessageChunk)):
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc.get("name"):
                            print(f"  [calling {tc['name']}...]", flush=True)
                elif msg.content:
                    print(msg.content, end="", flush=True)
        print()
