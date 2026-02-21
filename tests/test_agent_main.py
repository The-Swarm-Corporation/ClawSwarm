"""
Unit tests for claw_swarm.agent.main (create_agent, call_claude).
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch


from claw_swarm.agent import main as agent_main


class TestCallClaude:
    """Test call_claude."""

    def test_returns_joined_responses(self):
        with patch(
            "claw_swarm.agent.main.run_claude_agent",
            return_value=["First part.", "Second part."],
        ):
            result = agent_main.call_claude("Do something")
        assert result == "First part.\n\nSecond part."

    def test_filters_empty_responses(self):
        with patch(
            "claw_swarm.agent.main.run_claude_agent",
            return_value=["A", "", "B", ""],
        ):
            result = agent_main.call_claude("Task")
        assert result == "A\n\nB"

    def test_empty_responses_return_empty_string(self):
        with patch(
            "claw_swarm.agent.main.run_claude_agent",
            return_value=[],
        ):
            result = agent_main.call_claude("Task")
        assert result == ""

    def test_strips_whitespace(self):
        with patch(
            "claw_swarm.agent.main.run_claude_agent",
            return_value=["  ok  "],
        ):
            result = agent_main.call_claude("Task")
        assert result == "ok"

    def test_passes_task_to_run_claude_agent(self):
        with patch(
            "claw_swarm.agent.main.run_claude_agent",
            return_value=["done"],
        ) as m:
            agent_main.call_claude("my specific task")
        m.assert_called_once()
        call_kw = m.call_args[1]
        assert call_kw["tasks"] == "my specific task"
        assert "name" in call_kw
        assert "description" in call_kw
        assert "prompt" in call_kw


class TestCreateAgent:
    """Test create_agent (returns HierarchicalSwarm with director + workers)."""

    def test_returns_swarm_instance(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            mock_swarm.return_value = MagicMock()
            result = agent_main.create_agent()
        assert result is mock_swarm.return_value

    def test_uses_default_agent_name(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            agent_main.create_agent()
        call_kw = mock_swarm.call_args[1]
        assert call_kw["name"] == "ClawSwarm"
        assert call_kw["director_name"] == "ClawSwarm"
        assert call_kw["director"] is None

    def test_custom_agent_name(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            agent_main.create_agent(agent_name="CustomBot")
        call_kw = mock_swarm.call_args[1]
        assert call_kw["name"] == "CustomBot"
        assert call_kw["director_name"] == "CustomBot"

    def test_custom_system_prompt(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            agent_main.create_agent(
                system_prompt="Custom instructions."
            )
        call_kw = mock_swarm.call_args[1]
        assert (
            "Custom instructions."
            in call_kw["director_system_prompt"]
        )

    def test_director_uses_builtin_with_clawswarm_prompt(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            agent_main.create_agent()
        call_kw = mock_swarm.call_args[1]
        assert call_kw["director"] is None
        assert "director_system_prompt" in call_kw
        assert "ClawSwarm" in call_kw["director_system_prompt"]

    def test_swarm_has_worker_agents(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            agent_main.create_agent()
        call_kw = mock_swarm.call_args[1]
        assert call_kw["agents"] is agent_main.WORKER_AGENTS
        assert len(call_kw["agents"]) == 4
        assert call_kw["director"] is None

    def test_model_from_env(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            with patch.dict(
                os.environ, {"AGENT_MODEL": "gpt-4o"}, clear=False
            ):
                agent_main.create_agent()
        call_kw = mock_swarm.call_args[1]
        assert call_kw["director_model_name"] == "gpt-4o"

    def test_model_default_when_env_empty(self):
        with patch(
            "claw_swarm.agent.main.HierarchicalSwarm"
        ) as mock_swarm:
            with patch.dict(
                os.environ, {"AGENT_MODEL": ""}, clear=False
            ):
                agent_main.create_agent()
        call_kw = mock_swarm.call_args[1]
        assert call_kw["director_model_name"] == "gpt-4o-mini"
