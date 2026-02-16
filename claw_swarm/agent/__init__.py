"""
ClawSwarm main agent: a Swarms Agent with the ClawSwarm system prompt and Claude as a tool.

All prompts live in claw_swarm/prompts/ (clawswarm.md, claude_tool.md).
"""

from __future__ import annotations

import os
from pathlib import Path

from claw_swarm.tools import run_claude_agent


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = _prompts_dir() / f"{name}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _create_claude_tool():
    """Build the call_claude tool with the claude_tool prompt baked in."""
    claude_prompt = _load_prompt("claude_tool") or (
        "Execute the given task with full reasoning or code as needed. Return clear, complete responses."
    )

    def call_claude(task: str) -> str:
        """
        Delegate to Claude for deep reasoning, code generation, or long-form analysis.

        Use this tool when the user's request needs:
        - Multi-step reasoning or research
        - Code writing, debugging, or explanation
        - Detailed analysis or long-form answers

        Args:
            task: The exact task or question to send to Claude (e.g. "Write a Python function that..." or "Explain X in detail").

        Returns:
            str: Claude's full response. Summarize or quote this for the user in chat as needed.
        """
        responses = run_claude_agent(
            name="ClaudeHelper",
            description="Helper that executes tasks with full reasoning and code when invoked by ClawSwarm.",
            prompt=claude_prompt,
            tasks=task,
        )
        return "\n\n".join(r for r in responses if r).strip() if responses else ""

    return call_claude


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

    Loads the ClawSwarm system prompt from prompts/clawswarm.md and uses
    prompts/claude_tool.md for the Claude tool. Override with env or arguments.

    Args:
        model_name: LLM for the main agent (e.g. "gpt-4o-mini", "claude-3-5-sonnet-20241022").
                    Defaults to AGENT_MODEL env or "gpt-4o-mini".
        system_prompt: Override the loaded clawswarm prompt.
        agent_name: Agent identifier.
        agent_description: Short description (defaults to ClawSwarm role).
        max_loops: Max agent loops ("auto" or int).

    Returns:
        swarms.Agent instance ready for .run(task).
    """
    from swarms import Agent

    default_prompt = _load_prompt("clawswarm")
    prompt = system_prompt if system_prompt is not None else default_prompt
    if not prompt:
        prompt = (
            "You are ClawSwarm, a helpful assistant on Telegram, Discord, and WhatsApp. "
            "Respond concisely. Use the call_claude tool for deep reasoning or code."
        )

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
        tools=[_create_claude_tool()],
    )
