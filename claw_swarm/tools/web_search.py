"""Simple web search helper for ClawSwarm."""

from __future__ import annotations

from typing import Any

import httpx


def web_search(query: str, max_results: int = 5) -> str:
    """Run a lightweight DuckDuckGo search and return summarized text."""
    search_query = (query or "").strip()
    if not search_query:
        return "No query provided."

    try:
        response = httpx.get(
            "https://api.duckduckgo.com/",
            params={
                "q": search_query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
    except Exception as exc:
        return f"Web search failed: {exc!s}"

    payload: dict[str, Any] = response.json()
    lines: list[str] = []

    abstract = (payload.get("AbstractText") or "").strip()
    abstract_url = (payload.get("AbstractURL") or "").strip()
    if abstract:
        if abstract_url:
            lines.append(f"- {abstract} ({abstract_url})")
        else:
            lines.append(f"- {abstract}")

    def append_result(item: dict[str, Any]) -> None:
        text = (item.get("Text") or "").strip()
        url = (item.get("FirstURL") or "").strip()
        if text and url:
            lines.append(f"- {text} ({url})")

    for item in payload.get("Results", []) or []:
        if isinstance(item, dict):
            append_result(item)
        if len(lines) >= max_results:
            break

    if len(lines) < max_results:
        for item in payload.get("RelatedTopics", []) or []:
            if isinstance(item, dict) and "Topics" in item:
                for nested in item.get("Topics", []):
                    if isinstance(nested, dict):
                        append_result(nested)
                    if len(lines) >= max_results:
                        break
            elif isinstance(item, dict):
                append_result(item)
            if len(lines) >= max_results:
                break

    if not lines:
        return "No web results found."
    return "\n".join(lines[:max_results])
