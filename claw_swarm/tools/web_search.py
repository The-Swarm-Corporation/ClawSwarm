from __future__ import annotations

from typing import Any


def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Run a web search and return normalized lightweight results.

    Returns a list of objects with keys: title, url, snippet.
    """
    q = (query or "").strip()
    if not q:
        return []

    try:
        from duckduckgo_search import DDGS
    except Exception as exc:
        raise RuntimeError(
            "duckduckgo-search is not installed; install it to use web_search"
        ) from exc

    limit = max(1, min(int(max_results), 10))
    with DDGS() as ddgs:
        rows = ddgs.text(q, max_results=limit) or []
        out: list[dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "title": row.get("title", ""),
                    "url": row.get("href", ""),
                    "snippet": row.get("body", ""),
                }
            )
        return out
