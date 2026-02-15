"""
Claude agent utilities: run an agent with custom name, description, prompt, and tasks.
"""

from __future__ import annotations

import anyio
from typing import Any, AsyncIterator

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)

TOOLS_PRESET_CLAUDE_CODE: dict[str, Any] = {"type": "preset", "preset": "claude_code"}


async def run_claude_agent_async(
    name: str,
    description: str,
    prompt: str,
    tasks: str,
) -> list[str]:
    """
    Async version: run the Claude agent. Returns all assistant text responses as a list.

    Args:
        name: Identifier/name for this agent run.
        description: Short description of the agent's role.
        prompt: System prompt (agent instructions).
        tasks: The user's input / task to execute (sent to the agent).
    """
    texts: list[str] = []
    async for message in stream_claude_agent(
        name=name,
        description=description,
        prompt=prompt,
        tasks=tasks,
    ):
        texts.append(message)
    return texts


async def stream_claude_agent(
    name: str,
    description: str,
    prompt: str,
    tasks: str,
) -> AsyncIterator[str]:
    """
    Stream the Claude agent. Yields assistant text blocks as they arrive.

    Args:
        name: Identifier/name for this agent run.
        description: Short description of the agent's role.
        prompt: System prompt (agent instructions).
        tasks: The user's input / task to execute (sent to the agent).
    """
    combined_system = _build_system_prompt(
        name=name, description=description, system_prompt=prompt
    )

    opts = ClaudeAgentOptions(
        system_prompt=combined_system,
        max_turns=120,
        tools=TOOLS_PRESET_CLAUDE_CODE,
    )

    async for message in query(prompt=tasks, options=opts):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text:
                    yield block.text.strip()


def _build_system_prompt(name: str, description: str, system_prompt: str) -> str:
    """Combine name, description, and system prompt into one system message."""
    parts = [
        f"You are operating as the agent named: {name}.",
        f"Description of your role: {description}.",
        "",
        system_prompt.strip(),
    ]
    return "\n".join(parts).strip()


def run_claude_agent(
    name: str,
    description: str,
    prompt: str,
    tasks: str,
) -> list[str]:
    """
    Run the Claude agent with the given identity and task. Blocks until the run finishes.

    This is the main entry point for one-off agent runs. It creates a new Claude Code
    session, sends your system prompt (plus name and description) as agent instructions,
    and sends ``tasks`` as the user's input. The agent uses Claude Code's default tools
    (e.g. Read, Write, Edit, Bash, Grep, Glob) and up to 120 conversation turns.
    All assistant text replies are collected and returned as a list.

    Parameters
    ----------
    name : str
        Identifier or name for this agent run. Injected into the system context so the
        agent can identify itself (e.g. "CodeReviewer", "DataHelper").
    description : str
        Short, natural-language description of the agent's role. Injected into the system
        context so the agent knows how it should behave (e.g. "Reviews Python code for
        style and bugs").
    prompt : str
        Full system prompt: instructions, constraints, and style you want the agent to
        follow. This is the agent's "personality" and rules, not the user's request.
    tasks : str
        The user's request: the task or question to execute. This is sent as the user
        message (the ``prompt`` argument to the SDK's ``query()``).

    Returns
    -------
    list[str]
        All assistant text responses from the run, in order (one string per assistant
        message). Empty strings are omitted; each element is stripped of leading/trailing
        whitespace.

    Notes
    -----
    - Each call starts a new session; there is no conversation history across calls.
    - For streaming responses or multiple exchanges in one session, use
      ``stream_claude_agent`` or ``run_claude_agent_async`` instead.
    - Requires the Claude Code CLI (bundled with ``claude-agent-sdk`` or installed
      separately) and appropriate API access.

    Examples
    --------
    >>> responses = run_claude_agent(
    ...     name="Summarizer",
    ...     description="Summarizes long texts concisely.",
    ...     prompt="Respond in at most three bullet points. Be neutral and factual.",
    ...     tasks="Summarize the key risks in this project proposal.",
    ... )
    >>> for text in responses:
    ...     print(text)
    """
    return anyio.run(
        run_claude_agent_async(
            name=name,
            description=description,
            prompt=prompt,
            tasks=tasks,
        )
    )
