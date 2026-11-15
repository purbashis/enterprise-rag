"""Read-only API tool for a small allowlist of public demo/data APIs."""

import asyncio
import json
import logging
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

logger = logging.getLogger(__name__)

ALLOWED_API_HOSTS = {
    "api.github.com",
    "api.open-meteo.com",
    "jsonplaceholder.typicode.com",
}
MAX_RESPONSE_BYTES = 1_000_000


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


class ApiToolCallingAgent:
    """Call read-only HTTPS endpoints without arbitrary-host access."""

    def __init__(self) -> None:
        self._initialized = False

    async def initialize(self) -> None:
        self._initialized = True

    async def call(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[dict] = None,
    ) -> dict[str, Any]:
        try:
            parsed = urlparse(endpoint)
            port = parsed.port
        except ValueError as error:
            raise ValueError("Invalid API endpoint URL.") from error
        if (
            parsed.scheme != "https"
            or parsed.hostname not in ALLOWED_API_HOSTS
            or parsed.username
            or parsed.password
            or port not in (None, 443)
        ):
            raise ValueError(
                "API calls require HTTPS to api.github.com, api.open-meteo.com, "
                "or jsonplaceholder.typicode.com."
            )
        if method.upper() != "GET":
            raise ValueError("Only read-only GET API calls are supported.")

        if payload:
            query = parse_qsl(parsed.query, keep_blank_values=True) + [
                (str(key), str(value)) for key, value in payload.items()
            ]
            endpoint = urlunparse(parsed._replace(query=urlencode(query)))

        request = Request(
            endpoint,
            headers={
                "Accept": "application/json",
                "User-Agent": "LocalResearchAgent/1.0",
            },
            method="GET",
        )
        try:
            status, response_body = await asyncio.to_thread(self._fetch, request)
        except (URLError, TimeoutError) as error:
            logger.warning("Public API request failed for %s: %s", parsed.hostname, error)
            raise RuntimeError("The public API request failed.") from error

        try:
            body: Any = json.loads(response_body)
        except json.JSONDecodeError:
            body = {"raw_text": response_body}

        return {
            "endpoint": endpoint,
            "method": "GET",
            "status_code": status,
            "body": body,
            "agent": "api_caller",
        }

    @staticmethod
    def _fetch(request: Request) -> tuple[int, str]:
        opener = build_opener(_NoRedirect())
        try:
            response = opener.open(request, timeout=12)
        except HTTPError as error:
            response = error
        with response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise ValueError("API response exceeded the 1 MB limit.")
            return response.status, data.decode("utf-8", errors="replace")

    async def close(self) -> None:
        self._initialized = False

    def is_ready(self) -> bool:
        return self._initialized


_api_caller_agent: Optional[ApiToolCallingAgent] = None


def get_api_caller_agent() -> ApiToolCallingAgent:
    global _api_caller_agent
    if _api_caller_agent is None:
        _api_caller_agent = ApiToolCallingAgent()
    return _api_caller_agent
