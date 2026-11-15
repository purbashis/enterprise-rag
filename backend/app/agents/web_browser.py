"""Free web search via DuckDuckGo's HTML search page."""

import asyncio
import logging
from html.parser import HTMLParser
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class _SearchResultParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._active: dict[str, str] | None = None
        self._capture_snippet = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = attributes.get("class", "") or ""
        class_names = classes.split()
        if tag == "a" and {"result__a", "result-link"}.intersection(class_names):
            self._active = {
                "title": "",
                "url": self._result_url(attributes.get("href", "") or ""),
                "snippet": "",
            }
        elif {"result__snippet", "result-snippet"}.intersection(class_names):
            self._capture_snippet = True

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._active is not None and not self._active["title"]:
            self._active["title"] = text
        elif self._capture_snippet and self.results:
            self.results[-1]["snippet"] += f" {text}"

    def handle_endtag(self, tag: str) -> None:
        if self._active is not None and tag == "a":
            self.results.append(self._active)
            self._active = None
        if tag in ("a", "div", "td", "span", "p"):
            self._capture_snippet = False

    @staticmethod
    def _result_url(href: str) -> str:
        parsed = urlparse(href)
        if parsed.path == "/l/":
            return parse_qs(parsed.query).get("uddg", [""])[0]
        return href


class WebBrowserAgent:
    """Fetch real search results without a paid search API or browser runtime."""

    async def initialize(self) -> None:
        return None

    async def search(self, query: str, max_results: int = 5) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        if not 1 <= max_results <= 10:
            raise ValueError("max_results must be between 1 and 10.")

        started = asyncio.get_running_loop().time()
        params = urlencode({"q": query})
        request = Request(
            f"https://lite.duckduckgo.com/lite/?{params}",
            headers={"User-Agent": "Mozilla/5.0 (compatible; LocalResearchAgent/1.0)"},
        )
        try:
            html = await asyncio.to_thread(self._fetch, request)
        except URLError as error:
            logger.warning("DuckDuckGo search failed: %s", error)
            raise RuntimeError("Free web search is temporarily unavailable.") from error

        parser = _SearchResultParser()
        parser.feed(html)
        results = [
            {"title": result["title"], "url": result["url"], "snippet": result["snippet"].strip()}
            for result in parser.results
            if result["title"] and result["url"]
        ][:max_results]

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_time_ms": round((asyncio.get_running_loop().time() - started) * 1000, 2),
            "agent": "web_browser",
        }

    @staticmethod
    def _fetch(request: Request) -> str:
        with urlopen(request, timeout=12) as response:
            return response.read(2_000_001).decode("utf-8", errors="replace")

    def is_ready(self) -> bool:
        return True


_web_browser_agent: WebBrowserAgent | None = None


def get_web_browser_agent() -> WebBrowserAgent:
    global _web_browser_agent
    if _web_browser_agent is None:
        _web_browser_agent = WebBrowserAgent()
    return _web_browser_agent
