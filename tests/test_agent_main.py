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
    """Test create_agent."""

    def test_returns_agent_instance(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            mock_agent.return_value = MagicMock()
            result = agent_main.create_agent()
        assert result is mock_agent.return_value

    def test_uses_default_agent_name(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            agent_main.create_agent()
        call_kw = mock_agent.call_args[1]
        assert call_kw["agent_name"] == "ClawSwarm"

    def test_custom_agent_name(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            agent_main.create_agent(agent_name="CustomBot")
        call_kw = mock_agent.call_args[1]
        assert call_kw["agent_name"] == "CustomBot"

    def test_custom_system_prompt(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            agent_main.create_agent(
                system_prompt="Custom instructions."
            )
        call_kw = mock_agent.call_args[1]
        assert "Custom instructions." in call_kw["system_prompt"]

    def test_agent_config_max_loops_and_output_type(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            agent_main.create_agent()
        call_kw = mock_agent.call_args[1]
        assert call_kw["max_loops"] == 1
        assert call_kw["output_type"] == "final"

    def test_agent_has_tools(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            agent_main.create_agent()
        call_kw = mock_agent.call_args[1]
        assert "tools" in call_kw
        tools = call_kw["tools"]
        assert len(tools) >= 1
        # launch_token and claim_fees are in the list
        from claw_swarm.tools.launch_tokens import (
            claim_fees,
            launch_token,
        )

        assert launch_token in tools
        assert claim_fees in tools

    def test_model_from_env(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            with patch.dict(
                os.environ, {"AGENT_MODEL": "gpt-4o"}, clear=False
            ):
                agent_main.create_agent()
        call_kw = mock_agent.call_args[1]
        assert call_kw["model_name"] == "gpt-4o"

    def test_model_default_when_env_empty(self):
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            with patch.dict(
                os.environ, {"AGENT_MODEL": ""}, clear=False
            ):
                agent_main.create_agent()
        call_kw = mock_agent.call_args[1]
        assert call_kw["model_name"] == "gpt-4o-mini"

    def test_uses_config_values(self, tmp_path):
        cfg = tmp_path / "claw_swarm.toml"
        cfg.write_text(
            """
[agent]
name = "CfgBot"
description = "Cfg desc"
system_prompt = "Cfg prompt"
model = "gpt-4o"
max_tokens = 2048
temperature = 0.1
""".strip()
        )
        with patch("claw_swarm.agent.main.Agent") as mock_agent:
            with patch.dict(os.environ, {}, clear=True):
                agent_main.create_agent(config_path=str(cfg))
        call_kw = mock_agent.call_args[1]
        assert call_kw["agent_name"] == "CfgBot"
        assert call_kw["agent_description"] == "Cfg desc"
        assert "Cfg prompt" in call_kw["system_prompt"]
        assert call_kw["model_name"] == "gpt-4o"
        assert call_kw["max_tokens"] == 2048
        assert call_kw["temperature"] == 0.1
