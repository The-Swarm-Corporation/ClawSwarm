"""
ClawSwarm main agent: a Swarms Agent with the ClawSwarm system prompt and Claude as a tool.

This module provides utilities to create the ClawSwarm agent, which responds on platforms
like Telegram, Discord, and WhatsApp using a unified agent prompt and behavior.
The agent's behavior and context are defined by centralized prompt strings in
claw_swarm.prompts.

Key functionality:
- `call_claude`: Run a delegated reasoning, code, or analysis task via Claude (as a tool).
- `create_agent`: Construct a Swarms Agent preconfigured with system prompts and agent
  description suitable for general-purpose enterprise chat, research, and development.
  By default, the agent runs with a single loop and produces concise, final outputs
  appropriate for messaging platforms.

Agent prompt, helper tool context, and roles are imported from `claw_swarm.prompts`
to ensure all replies and tool usage are consistent and easy to maintain.

Usage:
    from claw_swarm.agent import create_agent, call_claude

    agent = create_agent()
    result = agent.run("Summarize today's AI news.")

    tool_response = call_claude("Write a Python function that reverses a string.")

See also:
    - claw_swarm.prompts (system/context strings)
    - claw_swarm.tools (Claude agent helpers)
"""

from __future__ import annotations

import os

from swarms import Agent

from claw_swarm.prompts import (
    CLAUDE_HELPER_DESCRIPTION,
    CLAUDE_HELPER_NAME,
    CLAUDE_TOOL_SYSTEM,
    CLAWSWARM_AGENT_DESCRIPTION,
    CLAWSWARM_SYSTEM,
    build_agent_system_prompt,
)
from claw_swarm.tools import run_claude_agent
from claw_swarm.tools.tools_registry import tools as registered_tools


def call_claude(task: str) -> str:
    """
    Run a specified task using Claude as the reasoning and coding engine.

    Args:
        task (str): The task or question for Claude to address. This can be
            long-form analysis, code generation, explanation, or complex multi-step reasoning.

    Returns:
        str: Claude's response(s), joined into a single string. Returns an empty string on failure.

    Example:
        >>> call_claude("Write a summary of the Python standard library.")
        'The Python standard library ...'
    """
    responses = run_claude_agent(
        name=CLAUDE_HELPER_NAME,
        description=CLAUDE_HELPER_DESCRIPTION,
        prompt=CLAUDE_TOOL_SYSTEM,
        tasks=task,
    )
    return (
        "\n\n".join(r for r in responses if r).strip()
        if responses
        else ""
    )


def create_agent(
    *,
    agent_name: str = "ClawSwarm",
    system_prompt: str | None = None,
) -> Agent:
    """
    Create the ClawSwarm Swarms Agent, preloaded with system prompts and
    configuration for enterprise chat, technical, and research use-cases.

    Args:
        agent_name (str): Name to assign the agent instance (shown in logs/UI).
        system_prompt (str | None): If provided, overrides the default ClawSwarm
            prompt (see `claw_swarm.prompts`). Otherwise, uses the enterprise
            ClawSwarm instructions, tuned for clarity and professionalism in chat.

    Returns:
        Agent: An instance of swarms.Agent ready for `.run(task)` calls.

    Config:
        - Model: from env AGENT_MODEL (default "gpt-4o-mini").
        - max_loops=1 (single-pass response, suitable for messaging platforms)
        - output_type="final" (concise, delivery-ready output)

    Example:
        >>> agent = create_agent()
        >>> reply = agent.run("What's new in Python 3.12?")
        >>> print(reply)
        'Python 3.12 introduces ...'
    """
    base_system = system_prompt or CLAWSWARM_SYSTEM
    # Combine name, description, and full instructions into one system message
    # so the model always sees who it is and its purpose (Swarms may not send
    # agent_name/agent_description to the LLM).
    full_system_prompt = build_agent_system_prompt(
        name=agent_name,
        description=CLAWSWARM_AGENT_DESCRIPTION,
        system_prompt=base_system,
    )

    model_name = (
        os.environ.get("AGENT_MODEL", "gpt-4o-mini").strip()
        or "gpt-4o-mini"
    )

    return Agent(
        agent_name=agent_name,
        agent_description=CLAWSWARM_AGENT_DESCRIPTION,
        system_prompt=full_system_prompt,
        model_name=model_name,
        max_loops=1,
        output_type="final",
        tools=registered_tools,
    )
