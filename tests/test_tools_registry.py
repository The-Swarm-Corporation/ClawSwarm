"""
Unit tests for tool integration in ClawSwarm.
"""

from __future__ import annotations

from unittest.mock import patch

from claw_swarm.agent import worker_agents
from claw_swarm.tools import tools_registry


def test_tools_registry_includes_web_search_and_scraping_tools():
    names = {getattr(t, "__name__", str(t)) for t in tools_registry.tools}
    assert "exa_search" in names
    assert "scrape_url" in names
    assert "scrape_urls" in names


def test_create_search_agent_registers_expected_tools():
    fake_search = lambda query: query
    with patch("claw_swarm.agent.worker_agents.Agent") as mock_agent:
        with patch(
            "claw_swarm.agent.worker_agents.exa_search", fake_search
        ):
            worker_agents.create_search_agent()

    call_kwargs = mock_agent.call_args.kwargs
    tools = call_kwargs["tools"]
    assert len(tools) == 3
    assert tools[0] is fake_search
    assert tools[1].__name__ == "scrape_url"
    assert tools[2].__name__ == "scrape_urls"
