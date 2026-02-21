"""
Unit tests for claw_swarm.tools.tools_registry and web_search.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from claw_swarm.tools import tools_registry
from claw_swarm.tools.web_search import web_search


def test_registry_contains_core_tools():
    names = {getattr(tool, "__name__", "") for tool in tools_registry.tools}
    assert "launch_token" in names
    assert "claim_fees" in names
    assert "run_claude_agent" in names
    assert "web_search" in names


def test_web_search_returns_empty_for_blank_query():
    assert web_search("   ") == []


def test_web_search_normalizes_results():
    fake_results = [
        {"title": "Result 1", "href": "https://a", "body": "one"},
        {"title": "Result 2", "href": "https://b", "body": "two"},
    ]
    ddgs = MagicMock()
    ddgs.text.return_value = fake_results

    manager = MagicMock()
    manager.__enter__.return_value = ddgs
    manager.__exit__.return_value = False

    with patch("duckduckgo_search.DDGS", return_value=manager):
        rows = web_search("python", max_results=2)

    assert rows == [
        {"title": "Result 1", "url": "https://a", "snippet": "one"},
        {"title": "Result 2", "url": "https://b", "snippet": "two"},
    ]
