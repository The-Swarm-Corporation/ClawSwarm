"""
ClawSwarm main agent: a Swarms Agent with the ClawSwarm system prompt and Claude as a tool.
"""

from __future__ import annotations

import os

from claw_swarm.prompts import CLAUDE_TOOL_SYSTEM, CLAWSWARM_SYSTEM
from claw_swarm.tools import run_claude_agent
from swarms_tools import exa_search


def call_claude(task: str) -> str:
    """Delegate to Claude for reasoning, code, or long-form analysis. Use for multi-step tasks, code, or detailed answers."""
    responses = run_claude_agent(
        name="ClaudeHelper",
        description="Helper that executes tasks with full reasoning and code when invoked by ClawSwarm.",
        prompt=CLAUDE_TOOL_SYSTEM,
        tasks=task,
    )
    return "\n\n".join(r for r in responses if r).strip() if responses else ""


def create_agent(
    *,
    model_name: str | None = None,
    system_prompt: str | None = None,
    agent_name: str = "ClawSwarm",
    agent_description: str | None = None,
    max_loops: int | str = "auto",
):
    """
    Create the ClawSwarm Swarms Agent with Claude as a tool.

    Uses prompts from claw_swarm.prompts. Override system_prompt to customize.

    Args:
        model_name: LLM for the main agent (e.g. "gpt-4o-mini", "claude-3-5-sonnet-20241022").
                    Defaults to AGENT_MODEL env or "gpt-4o-mini".
        system_prompt: Override the default system prompt.
        agent_name: Agent identifier.
        agent_description: Short description (defaults to ClawSwarm role).
        max_loops: Max agent loops ("auto" or int).

    Returns:
        swarms.Agent instance ready for .run(task).
    """
    from swarms import Agent

    prompt = system_prompt if system_prompt is not None else CLAWSWARM_SYSTEM

    model = model_name or os.environ.get("AGENT_MODEL", "gpt-4o-mini")
    description = agent_description or (
        "Enterprise-grade assistant that responds on Telegram, Discord, and WhatsApp; "
        "uses Claude as a tool for deep reasoning and code."
    )

    return Agent(
        agent_name=agent_name,
        agent_description=description,
        system_prompt=prompt,
        model_name=model,
        max_loops=max_loops,
        tools=[call_claude, exa_search],
    )
