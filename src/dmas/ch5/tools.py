from __future__ import annotations

import base64
from dataclasses import dataclass, field
from types import TracebackType


@dataclass
class BrowserSession:
    """Async context manager wrapping a Playwright browser and page."""

    headless: bool = True
    _playwright: object = field(default=None, init=False, repr=False)
    _browser: object = field(default=None, init=False, repr=False)
    page: object = field(default=None, init=False, repr=False)

    async def __aenter__(self) -> BrowserSession:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. Install it with:\n"
                "  pip install 'dmas[computer-use]'\n"
                "  playwright install chromium"
            )
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self.page = await self._browser.new_page(viewport={"width": 1280, "height": 720})
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


async def navigate(session: BrowserSession, url: str) -> str:
    """Navigate the browser to a URL.

    Args:
        url: The URL to navigate to (e.g. "https://example.com").
    """
    await session.page.goto(url, wait_until="domcontentloaded")
    return f"Navigated to {url}"


async def click(session: BrowserSession, selector: str) -> str:
    """Click an element on the page.

    Args:
        selector: CSS selector for the element to click (e.g. "button.submit").
    """
    try:
        await session.page.click(selector, timeout=5000)
        return f"Clicked: {selector}"
    except Exception as exc:
        return f"Click failed on '{selector}': {exc}"


async def type_text(session: BrowserSession, selector: str, text: str) -> str:
    """Type text into an input field.

    Args:
        selector: CSS selector for the input element.
        text: The text to type into the field.
    """
    try:
        await session.page.fill(selector, text)
        return f"Typed into '{selector}': {text}"
    except Exception as exc:
        return f"Type failed on '{selector}': {exc}"


async def scroll(session: BrowserSession, direction: str, amount: int = 300) -> str:
    """Scroll the page up or down.

    Args:
        direction: Scroll direction — "up" or "down".
        amount: Number of pixels to scroll (default 300).
    """
    delta = amount if direction == "down" else -amount
    await session.page.mouse.wheel(0, delta)
    return f"Scrolled {direction} by {amount}px"


async def observe_page(session: BrowserSession) -> str:
    """Observe the current page state: title, URL, visible text, and interactive elements."""
    title = await session.page.title()
    url = session.page.url
    text = await session.page.inner_text("body")
    text = text[:3000]

    # Collect interactive elements
    elements = await session.page.query_selector_all(
        "a, button, input, select, textarea, [role='button'], [role='link']"
    )
    interactive = []
    for el in elements[:30]:
        tag = await el.evaluate("el => el.tagName.toLowerCase()")
        el_text = (await el.inner_text()).strip()[:50] if await el.is_visible() else ""
        el_type = await el.get_attribute("type") or ""
        el_href = await el.get_attribute("href") or ""
        el_id = await el.get_attribute("id") or ""
        el_class = await el.get_attribute("class") or ""

        desc = tag
        if el_id:
            desc += f"#{el_id}"
        if el_class:
            first_class = el_class.split()[0]
            desc += f".{first_class}"
        if el_type:
            desc += f"[type={el_type}]"
        if el_href:
            desc += f" -> {el_href[:60]}"
        if el_text:
            desc += f' "{el_text[:40]}"'
        interactive.append(desc)

    parts = [
        f"Title: {title}",
        f"URL: {url}",
        f"\n--- Page Text (truncated) ---\n{text}",
    ]
    if interactive:
        parts.append("\n--- Interactive Elements ---")
        for i, el_desc in enumerate(interactive, 1):
            parts.append(f"  {i}. {el_desc}")

    return "\n".join(parts)


async def screenshot(session: BrowserSession) -> str:
    """Take a screenshot of the current page and return it as a base64-encoded PNG."""
    png_bytes = await session.page.screenshot()
    return base64.b64encode(png_bytes).decode("ascii")
