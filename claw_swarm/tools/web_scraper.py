"""
Web scraper tool for ClawSwarm agents.

Fetches and returns the readable text content of one or more URLs.
Uses httpx for HTTP (already a project dependency) and the stdlib
html.parser to strip markup — no extra dependencies required.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Union

import httpx

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SKIP_TAGS = {
    "script",
    "style",
    "noscript",
    "head",
    "meta",
    "link",
    "iframe",
    "svg",
    "path",
}

_DEFAULT_TIMEOUT = 15  # seconds


class _TextExtractor(HTMLParser):
    """Minimal HTML → plain-text extractor using the stdlib parser."""

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        raw = " ".join(self._parts)
        raw = html.unescape(raw)
        # collapse whitespace
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _fetch_text(url: str, timeout: int = _DEFAULT_TIMEOUT) -> str:
    """Fetch *url* and return its readable text content."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; ClawSwarm-Scraper/1.0; "
            "+https://github.com/The-Swarm-Corporation/ClawSwarm)"
        )
    }
    with httpx.Client(
        follow_redirects=True, timeout=timeout, headers=headers
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "html" in content_type or "text" in content_type:
            extractor = _TextExtractor()
            extractor.feed(resp.text)
            return extractor.get_text()
        # Non-HTML (JSON, plain-text, etc.) — return as-is
        return resp.text


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------


def scrape_url(url: str) -> str:
    """
    Fetch and return the readable text content of a single web page.

    Args:
        url: The full URL to scrape (e.g. "https://example.com/page").

    Returns:
        The visible text extracted from the page, or an error message
        prefixed with "ERROR:" if the request fails.
    """
    try:
        return _fetch_text(url)
    except httpx.HTTPStatusError as exc:
        return f"ERROR: HTTP {exc.response.status_code} for {url}"
    except httpx.RequestError as exc:
        return f"ERROR: Request failed for {url}: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: Unexpected error scraping {url}: {exc}"


def scrape_urls(urls: Union[list[str], str]) -> str:
    """
    Fetch and return the readable text content of one or more URLs.

    Pass a list of URL strings, or a newline/comma-separated string of
    URLs. Results are returned as a single string with each URL's
    content clearly delimited.

    Args:
        urls: A list of URL strings, or a newline- or comma-separated
              string of URLs.

    Returns:
        Concatenated text content for all URLs, each section prefixed
        with "=== <url> ===" and separated by blank lines.
    """
    if isinstance(urls, str):
        # Accept comma- or newline-separated URLs as a plain string
        urls = [
            u.strip() for u in re.split(r"[\n,]+", urls) if u.strip()
        ]

    if not urls:
        return "ERROR: No URLs provided."

    parts: list[str] = []
    for url in urls:
        content = scrape_url(url)
        parts.append(f"=== {url} ===\n{content}")

    return "\n\n".join(parts)
