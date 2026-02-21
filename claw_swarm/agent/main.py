from __future__ import annotations

import os

import re

from swarms import Agent, HierarchicalSwarm
from swarms.prompts.hiearchical_system_prompt import (
    HIEARCHICAL_SWARM_SYSTEM_PROMPT,
)
import traceback
from claw_swarm.prompts import (
    CLAUDE_HELPER_DESCRIPTION,
    CLAUDE_HELPER_NAME,
    CLAUDE_TOOL_SYSTEM,
    CLAWSWARM_AGENT_DESCRIPTION,
    CLAWSWARM_SYSTEM,
    TELEGRAM_SUMMARY_SYSTEM,
    build_agent_system_prompt,
)
from claw_swarm.tools import run_claude_agent
from claw_swarm.agent.worker_agents import (
    create_developer_agent,
    create_response_agent,
    create_search_agent,
    create_token_launch_agent,
)

WORKER_AGENTS = [
    create_response_agent(),
    create_developer_agent(),
    create_search_agent(),
    create_token_launch_agent(),
]


def _build_director_system_prompt(
    *,
    agent_name: str = "ClawSwarm",
    system_prompt: str | None = None,
) -> str:
    """
    Build the director system prompt: ClawSwarm identity and behavior first,
    then the hierarchical director instructions so the director still outputs
    plan/orders in the format HierarchicalSwarm.parse_orders expects (SwarmSpec).
    """
    base_system = system_prompt or CLAWSWARM_SYSTEM
    clawswarm_part = build_agent_system_prompt(
        name=agent_name,
        description=CLAWSWARM_AGENT_DESCRIPTION,
        system_prompt=base_system,
    )
    return (
        clawswarm_part
        + "\n\n---\n\nYou are also the Hierarchical Agent Director. "
        "You MUST output your plan and orders using the SwarmSpec tool/schema "
        "so the swarm can execute them. Do not reply with plain text only.\n\n"
        + HIEARCHICAL_SWARM_SYSTEM_PROMPT
    )


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
) -> HierarchicalSwarm:
    """
    Create the ClawSwarm hierarchical swarm: a director agent plus worker agents
    (search, token launch, developer). Use for enterprise chat, technical, and
    research use-cases with delegation to specialists.

    The director uses the ClawSwarm system prompt and the swarm's built-in
    director (SwarmSpec output) so plan/orders are parsed correctly.

    Args:
        agent_name (str): Name for the swarm and director (shown in logs/UI).
        system_prompt (str | None): If provided, overrides the default ClawSwarm
            prompt for the director (see `claw_swarm.prompts`).

    Returns:
        HierarchicalSwarm: Swarm ready for `.run(task)` calls. The director
            delegates to worker agents (search, token launch, developer).

    Example:
        >>> swarm = create_agent()
        >>> reply = swarm.run("What's new in Python 3.12?")
        >>> print(reply)
        'Python 3.12 introduces ...'
    """
    director_system_prompt = _build_director_system_prompt(
        agent_name=agent_name,
        system_prompt=system_prompt,
    )
    director_model_name = (
        os.environ.get("AGENT_MODEL", "gpt-4o-mini").strip()
        or "gpt-4o-mini"
    )
    return HierarchicalSwarm(
        name=agent_name,
        description="A hierarchical swarm of agents that can handle complex tasks",
        agents=WORKER_AGENTS,
        director_name=agent_name,
        director_model_name=director_model_name,
        director_system_prompt=director_system_prompt,
        director_feedback_on=False,
    )


def hierarchical_swarm(task: str):
    """
    Execute a task using the ClawSwarm hierarchical swarm (convenience wrapper).

    Args:
        task (str): The main task or instruction to be performed by the swarm.

    Returns:
        Any: The result returned by the swarm, or None on exception.
    """
    try:
        return create_agent().run(task)
    except Exception as e:
        print(
            f"Error running hierarchical_swarm: {e}\n{traceback.format_exc()}"
        )
        return None


# Emoji pattern for stripping any that slip through the summarizer
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "]+",
    flags=re.UNICODE,
)


def _create_telegram_summarizer_agent() -> Agent:
    """Create an agent that summarizes long output for Telegram (no emojis)."""
    return Agent(
        agent_name="ClawSwarm-TelegramSummarizer",
        agent_description="Summarizes swarm output for Telegram chat; no emojis.",
        system_prompt=TELEGRAM_SUMMARY_SYSTEM,
        model_name="gpt-4.1",
        max_loops=1,
    )


def summarize_for_telegram(swarm_output: str) -> str:
    """
    Take the raw output from the hierarchical swarm and return a concise
    summary suitable for Telegram, with no emojis.

    Args:
        swarm_output: Raw string output from the swarm (may be long or
            multi-part). If it's not a string (e.g. list from feedback_director),
            pass str(swarm_output).

    Returns:
        Summarized text for Telegram, with emojis stripped. Returns the
        original string (with emojis stripped) if summarization fails.
    """
    if not swarm_output or not str(swarm_output).strip():
        return ""
    
    summarizer = _create_telegram_summarizer_agent()
    
    out = summarizer.run(
        f"Summarize the following output for a Telegram message. No emojis.\n\n{swarm_output}"
    )
    
    return out