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

from claw_swarm.config import load_agent_config
from claw_swarm.prompts import (
    CLAUDE_HELPER_DESCRIPTION,
    CLAUDE_HELPER_NAME,
    CLAUDE_TOOL_SYSTEM,
    CLAWSWARM_AGENT_DESCRIPTION,
    CLAWSWARM_SYSTEM,
    build_agent_system_prompt,
)
from claw_swarm.tools import run_claude_agent, web_search
from claw_swarm.tools.launch_tokens import claim_fees, launch_token


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
    config_path: str | None = None,
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
    config = load_agent_config(config_path)

    configured_name = agent_name
    if agent_name == "ClawSwarm" and config and config.name:
        configured_name = config.name

    configured_description = CLAWSWARM_AGENT_DESCRIPTION
    if config and config.description:
        configured_description = config.description

    if system_prompt:
        base_system = system_prompt
    elif config and config.system_prompt:
        base_system = config.system_prompt
    else:
        base_system = CLAWSWARM_SYSTEM

    # Combine name, description, and full instructions into one system message
    # so the model always sees who it is and its purpose (Swarms may not send
    # agent_name/agent_description to the LLM).
    full_system_prompt = build_agent_system_prompt(
        name=configured_name,
        description=configured_description,
        system_prompt=base_system,
    )

    if config and config.model:
        default_model = config.model
    else:
        default_model = "gpt-4o-mini"
    model_name = os.environ.get("AGENT_MODEL", default_model).strip()
    if not model_name:
        model_name = default_model

    agent_kwargs = {
        "agent_name": configured_name,
        "agent_description": configured_description,
        "system_prompt": full_system_prompt,
        "model_name": model_name,
        "max_loops": 1,
        "output_type": "final",
        "tools": [launch_token, claim_fees, call_claude, web_search],
    }
    if config and config.max_tokens is not None:
        agent_kwargs["max_tokens"] = config.max_tokens
    if config and config.temperature is not None:
        agent_kwargs["temperature"] = config.temperature

    return Agent(**agent_kwargs)
