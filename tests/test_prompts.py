"""
Unit tests for claw_swarm.prompts.
"""

from __future__ import annotations


from claw_swarm.agent.prompts import (
    AGENT_DESCRIPTION_PREFIX,
    AGENT_NAME_PREFIX,
    CLAUDE_HELPER_DESCRIPTION,
    CLAUDE_HELPER_NAME,
    CLAUDE_TOOL_SYSTEM,
    CLAWSWARM_AGENT_DESCRIPTION,
    CLAWSWARM_IDENTITY_PREFIX,
    CLAWSWARM_SYSTEM,
    build_agent_system_prompt,
)


class TestPromptConstants:
    """Test that prompt constants are non-empty and have expected content."""

    def test_clawswarm_system_contains_identity(self):
        assert "ClawSwarm" in CLAWSWARM_SYSTEM
        assert "enterprise" in CLAWSWARM_SYSTEM.lower()

    def test_clawswarm_system_mentions_tools(self):
        assert (
            "exa_search" in CLAWSWARM_SYSTEM
            or "tool" in CLAWSWARM_SYSTEM.lower()
        )
        assert "call_claude" in CLAWSWARM_SYSTEM

    def test_clawswarm_agent_description_non_empty(self):
        assert len(CLAWSWARM_AGENT_DESCRIPTION) > 0
        assert "ClawSwarm" in CLAWSWARM_AGENT_DESCRIPTION

    def test_clawswarm_identity_prefix_contains_name(self):
        assert "ClawSwarm" in CLAWSWARM_IDENTITY_PREFIX
        assert "Assistant" in CLAWSWARM_IDENTITY_PREFIX

    def test_claude_tool_system_non_empty(self):
        assert len(CLAUDE_TOOL_SYSTEM) > 0
        assert "helper" in CLAUDE_TOOL_SYSTEM.lower()

    def test_claude_helper_name(self):
        assert CLAUDE_HELPER_NAME == "ClaudeHelper"

    def test_claude_helper_description_non_empty(self):
        assert len(CLAUDE_HELPER_DESCRIPTION) > 0

    def test_agent_name_prefix_has_placeholder(self):
        assert "{name}" in AGENT_NAME_PREFIX

    def test_agent_description_prefix_has_placeholder(self):
        assert "{description}" in AGENT_DESCRIPTION_PREFIX


class TestBuildAgentSystemPrompt:
    """Test build_agent_system_prompt."""

    def test_returns_combined_string(self):
        result = build_agent_system_prompt(
            name="TestAgent",
            description="A test agent.",
            system_prompt="Do things.",
        )
        assert "TestAgent" in result
        assert "A test agent." in result
        assert "Do things." in result

    def test_name_and_description_appear_first(self):
        result = build_agent_system_prompt(
            name="Alpha",
            description="Beta",
            system_prompt="Gamma",
        )
        lines = result.split("\n")
        assert any("Alpha" in line for line in lines)
        assert any("Beta" in line for line in lines)
        assert "Gamma" in result

    def test_strips_whitespace(self):
        result = build_agent_system_prompt(
            name="X",
            description="Y",
            system_prompt="  Z  \n",
        )
        assert result.startswith("You are")
        assert result.strip() == result

    def test_empty_system_prompt_allowed(self):
        result = build_agent_system_prompt(
            name="N",
            description="D",
            system_prompt="",
        )
        assert "N" in result
        assert "D" in result
