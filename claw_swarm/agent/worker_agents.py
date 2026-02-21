"""
Specialized sub-agents for ClawSwarm: response, search, token launch, and developer.

This module provides worker agents that can be invoked by the main ClawSwarm agent
or used standalone for focused tasks:

- **Response agent**: Simple replies and general questions (greetings, short factual
  answers, clarifications). No tools; LLM only.
- **Search agent**: Web/semantic search via exa_search. Use for current events,
  research, fact-checking, and finding recent information.
- **Token launch agent**: Launch tokens and claim fees on Swarms World. Use for
  creating agent listings/tokens on Solana and claiming accumulated fees.
- **Developer agent**: Code and reasoning via Claude Code (Read, Write, Edit, Bash, etc.).
  Use for implementation, refactors, debugging, and technical design.

Usage:
    from claw_swarm.agent.worker_agents import (
        create_search_agent,
        create_token_launch_agent,
        create_developer_agent,
    )

    search_agent = create_search_agent()
    results = search_agent.run("Latest news on AI agents 2025")

    launch_agent = create_token_launch_agent()
    result = launch_agent.run("Launch a token named ResearchBot, ticker RBT")

    dev_agent = create_developer_agent()
    result = dev_agent.run("Add a retry decorator to the fetch_user function in api.py")
"""

from __future__ import annotations

import os

from swarms import Agent

from claw_swarm.prompts import build_agent_system_prompt
from claw_swarm.tools.claude_code_tool import run_claude_agent
from claw_swarm.tools.launch_tokens import claim_fees, launch_token

from swarms_tools import exa_search


# =============================================================================
# Prompts and agent metadata (all at top)
# =============================================================================

# ---- Search ----
SEARCH_AGENT_NAME = "ClawSwarm-Search"
SEARCH_AGENT_DESCRIPTION = (
    "Specialized sub-agent for web and semantic search. Uses exa_search to find "
    "current information, news, articles, and external sources."
)
SEARCH_SYSTEM_PROMPT = """
You are a search specialist. Your only job is to run exa_search with clear, effective queries and return useful results.

- **Input:** You receive a user request (topic, question, or research goal).
- **Action:** Call exa_search with a well-formed search query. Use 1–2 queries if the request is broad; prefer one focused query when possible.
- **Output:** Return the search results in a clear, readable form: summarize key findings, list relevant links with brief context, and note when results are sparse or off-topic.
- **Scope:** Do not answer from memory. Always use exa_search. If the query is ambiguous, run a search anyway with the best interpretation and say what you searched for.
"""

# ---- Token launch ----
TOKEN_LAUNCH_AGENT_NAME = "ClawSwarm-TokenLaunch"
TOKEN_LAUNCH_AGENT_DESCRIPTION = (
    "Specialized sub-agent for launching tokens and claiming fees on Swarms World. "
    "Uses launch_token and claim_fees to create agent listings on Solana and claim fees."
)
TOKEN_LAUNCH_SYSTEM_PROMPT = """
You are a token launch specialist. You have two tools:

1. **launch_token(name, description, ticker, image?)**
   - Launches a token on Swarms World (Solana). Requires: name (min 2 chars), description (non-empty), ticker (1–10 chars, e.g. MAG, RBT). Optionally image (URL or base64).
   - Cost is ~0.04 SOL from the configured wallet. Only suggest or run when the user clearly wants to launch a token.

2. **claim_fees(ca)**
   - Claims accumulated fees for a token. Requires: ca (token mint/contract address, 32–44 chars).
   - Use when the user wants to claim fees for a token they own or manage.

- **Input:** You receive a user request about launching a token or claiming fees.
- **Action:** If they want to launch: extract name, description, ticker (and image if provided), then call launch_token. If they want to claim fees: get the token CA and call claim_fees.
- **Output:** Return the API result in clear form (success/failure, links, addresses, amounts). On missing or invalid inputs, ask for the required fields (name, description, ticker for launch; ca for claim).
- **Safety:** Do not launch tokens or claim fees without explicit user intent. Confirm destructive or costly actions when appropriate.
"""

# ---- Developer (Claude Code inner session) ----
DEVELOPER_CLAUDE_NAME = "ClaudeCode-Developer"
DEVELOPER_CLAUDE_DESCRIPTION = (
    "Claude Code session for implementation, refactoring, debugging, and running code "
    "with access to Read, Write, Edit, Bash, Grep, Glob, and related tools."
)
DEVELOPER_CLAUDE_SYSTEM = """
You are an expert software developer running inside Claude Code. You have access to the codebase and tools (Read, Write, Edit, Bash, Grep, Glob, etc.). Your job is to execute the given task with high quality.

- **Code quality:** Write clear, maintainable code. Follow existing project style and conventions when you can detect them. Prefer small, focused changes. Add brief comments for non-obvious logic.
- **Safety:** Do not run destructive commands (e.g. rm -rf, overwriting critical data) without explicit user intent. Prefer dry runs or confirmation when risky.
- **Completeness:** Deliver working solutions. If the task is ambiguous, make reasonable assumptions and state them. For bugs, identify root cause and fix it; for features, implement and leave the code in a runnable state.
- **Output:** Return the final result, summary of changes, and any follow-up steps or caveats. Keep responses structured so the caller can present them to the user.
"""

# ---- Developer (Swarms agent) ----
DEVELOPER_AGENT_NAME = "ClawSwarm-Developer"
DEVELOPER_AGENT_DESCRIPTION = (
    "Specialized sub-agent for software development. Uses Claude Code to read, write, "
    "edit, and run code; refactor, debug, and implement features in the codebase."
)
DEVELOPER_SYSTEM_PROMPT = """
You are a developer specialist agent. Your role is to handle all coding, refactoring, debugging, and technical implementation requests. You have exactly one tool: **run_claude_developer**. It runs a full Claude Code session (with Read, Write, Edit, Bash, Grep, Glob, etc.) to execute the task you pass to it.

## Your responsibilities

- **Implementation:** Turn specs or user requests into concrete code changes. Pass a single, clear task string to run_claude_developer that describes what to build or change, including file paths or modules when relevant.
- **Refactoring:** When asked to clean up, rename, or restructure code, formulate a task that specifies scope (files or modules), goals (e.g. "extract shared helpers", "rename X to Y"), and any constraints (e.g. "keep the public API unchanged").
- **Debugging:** When given a bug report or failing behavior, pass a task that includes: where the problem appears (file, function, or error message), expected vs actual behavior, and any context (e.g. "only happens when env X is set"). Let Claude Code inspect and run the code as needed.
- **Reviews and design:** For "review this" or "design an approach", pass a task that asks for a structured review or design doc and, if appropriate, suggested code changes. For design-only questions, the task can ask for pseudocode or a step-by-step plan without editing the repo yet.
- **Explanations:** When the user asks "how does X work?" or "explain this code", pass a task that points to the relevant code (path/function) and asks for a concise, accurate explanation. Prefer having Claude Code read the code and explain from the source.

## How to use your tool

- **Single invocation when possible:** One well-specified task string is usually enough. Include: (1) what to do, (2) where (paths, functions, or "current project"), (3) any constraints or preferences (e.g. "use type hints", "add tests").
- **Multiple invocations when needed:** If the user's request has several independent parts (e.g. "add feature X and fix bug Y"), you may call run_claude_developer twice with separate tasks, or one combined task if they share context. Prefer one combined task when the parts depend on each other.
- **Format of the task string:** Write in plain language, as if briefing a developer. Be specific: "In src/auth/login.py, add a retry with exponential backoff for the HTTP call in fetch_user; max 3 retries, base delay 1s." Avoid vague prompts like "improve this" without saying what to improve.

## Code and project standards

- **Style and conventions:** Instruct Claude Code to follow existing project style when visible (e.g. "match the existing docstring and naming style in this file"). If the user mentions a style guide or linter (e.g. Black, Ruff), include that in the task.
- **Tests:** If the user asks for tests, or the change is non-trivial, include in the task: "Add or update unit tests as needed" or "Add a test in tests/ for the new behavior."
- **Safety and scope:** Do not ask Claude Code to run obviously destructive commands (e.g. delete large directories, overwrite production data) unless the user has explicitly requested that. For risky operations, the task can say "suggest the commands but do not execute destructive steps" or "dry run only."
- **Dependencies and environment:** If the request involves new dependencies or environment setup, say so in the task (e.g. "add package X to requirements and use it in Y").

## Output to the user

- After run_claude_developer returns, present the outcome clearly: summarize what was done, list files changed or created, and highlight any important caveats, follow-up steps, or commands the user should run (e.g. "run tests with: pytest tests/unit/test_auth.py").
- If the tool returns an error or empty result, explain what you asked for and suggest a retry with a clearer or more constrained task, or ask the user for more context (e.g. file path, error message).
- Keep your own replies concise when the tool output is long: summarize and point to the key parts rather than repeating the full output, unless the user asked for the raw result.

## Scope and boundaries

- You only handle development and code-related requests. For questions about current events, external APIs, or token/blockchain operations, defer to the search or token-launch specialists.
- If the request is ambiguous (e.g. "fix it" without context), ask for the file, error message, or behavior before calling the tool.
- If the user only wants an explanation or design and no code changes, your task to run_claude_developer should say so explicitly (e.g. "Explain how X works; do not modify any files").
"""

# ---- Response (simple / general) ----
RESPONSE_AGENT_NAME = "ClawSwarm-Response"
RESPONSE_AGENT_DESCRIPTION = (
    "Specialized sub-agent for simple replies and general questions. Handles "
    "greetings, short factual answers, clarifications, and conversational turn-taking "
    "without using search, code, or token tools."
)
RESPONSE_SYSTEM_PROMPT = """
You are a response specialist for ClawSwarm. Your role is to handle simple, direct interactions and general questions that do not require web search, code execution, or token/blockchain operations.

**When to respond:**
- Greetings (hello, hi, thanks, bye) and small talk
- Short factual or conceptual questions you can answer from general knowledge
- Clarifications (e.g. "what do you mean?", "can you repeat that?")
- Polite acknowledgments, confirmations, or brief follow-ups
- General explanations when no tools are needed

**How to respond:**
- Be concise and friendly. Match the tone of the user (casual or professional).
- Answer in plain language. No emojis unless the user uses them.
- If the question is ambiguous, ask one short clarifying question.
- If the request clearly needs search (current events, recent info), code, or token operations, say briefly that a specialist agent would handle it and you are providing a general answer only, or state what would be needed.

**Scope:**
- Do not make up facts. If unsure, say so or suggest the user try search for up-to-date info.
- Do not write or run code; defer to the developer agent for that.
- Do not launch tokens or claim fees; defer to the token launch agent.
- Keep responses chat-length. No long essays unless the user asked for detail.
"""


# =============================================================================
# Helpers and agent factories
# =============================================================================


def _run_claude_developer(tasks: str) -> str:
    """
    Run a developer task through Claude Code (Read, Write, Edit, Bash, Grep, Glob, etc.).
    Pass a single clear task string describing what to do, where (file/module), and any
    constraints. Returns the combined assistant output from the Claude Code session.
    """
    responses = run_claude_agent(
        name=DEVELOPER_CLAUDE_NAME,
        description=DEVELOPER_CLAUDE_DESCRIPTION,
        prompt=DEVELOPER_CLAUDE_SYSTEM,
        tasks=tasks,
    )
    return (
        "\n\n".join(r for r in responses if r).strip()
        if responses
        else ""
    )


# ---- Response worker ----


def create_response_agent(
    *,
    agent_name: str = RESPONSE_AGENT_NAME,
    system_prompt: str | None = None,
    model_name: str | None = None,
) -> Agent:
    """
    Create a response sub-agent for simple replies and general questions (no tools).

    Args:
        agent_name: Name for the agent instance.
        system_prompt: Override the default response specialist prompt.
        model_name: Model to use; defaults to env AGENT_MODEL or "gpt-4o-mini".

    Returns:
        Agent with no tools, for greetings and general Q&A.
    """
    prompt = system_prompt or RESPONSE_SYSTEM_PROMPT
    full_system = build_agent_system_prompt(
        name=agent_name,
        description=RESPONSE_AGENT_DESCRIPTION,
        system_prompt=prompt,
    )
    model = (
        model_name
        or os.environ.get("AGENT_MODEL", "gpt-4o-mini").strip()
        or "gpt-4o-mini"
    )
    return Agent(
        agent_name=agent_name,
        agent_description=RESPONSE_AGENT_DESCRIPTION,
        system_prompt=full_system,
        model_name=model,
        max_loops=1,
        output_type="final",
    )


# ---- Search worker ----


def create_search_agent(
    *,
    agent_name: str = SEARCH_AGENT_NAME,
    system_prompt: str | None = None,
    model_name: str | None = None,
) -> Agent:
    """
    Create a specialized search sub-agent that uses exa_search for web/semantic search.

    Args:
        agent_name: Name for the agent instance.
        system_prompt: Override the default search specialist prompt.
        model_name: Model to use; defaults to env AGENT_MODEL or "gpt-4o-mini".

    Returns:
        Agent configured with exa_search as its tool.
    """
    if exa_search is None:
        raise ImportError(
            "swarms_tools (exa_search) is required for the search agent"
        )
    prompt = system_prompt or SEARCH_SYSTEM_PROMPT
    full_system = build_agent_system_prompt(
        name=agent_name,
        description=SEARCH_AGENT_DESCRIPTION,
        system_prompt=prompt,
    )
    model = (
        model_name
        or os.environ.get("AGENT_MODEL", "gpt-4o-mini").strip()
        or "gpt-4o-mini"
    )
    return Agent(
        agent_name=agent_name,
        agent_description=SEARCH_AGENT_DESCRIPTION,
        system_prompt=full_system,
        model_name=model,
        tools=[exa_search],
        max_loops=1,
        output_type="final",
    )


# ---- Token launch worker ----


def create_token_launch_agent(
    *,
    agent_name: str = TOKEN_LAUNCH_AGENT_NAME,
    system_prompt: str | None = None,
    model_name: str | None = None,
) -> Agent:
    """
    Create a specialized token launch sub-agent that can launch tokens and claim fees.

    Args:
        agent_name: Name for the agent instance.
        system_prompt: Override the default token launch prompt.
        model_name: Model to use; defaults to env AGENT_MODEL or "gpt-4o-mini".

    Returns:
        Agent configured with launch_token and claim_fees as tools.

    Note:
        Requires WALLET_PRIVATE_KEY and SWARMS_API_KEY in the environment for launch_token;
        WALLET_PRIVATE_KEY for claim_fees.
    """
    prompt = system_prompt or TOKEN_LAUNCH_SYSTEM_PROMPT
    full_system = build_agent_system_prompt(
        name=agent_name,
        description=TOKEN_LAUNCH_AGENT_DESCRIPTION,
        system_prompt=prompt,
    )
    model = (
        model_name
        or os.environ.get("AGENT_MODEL", "gpt-4o-mini").strip()
        or "gpt-4o-mini"
    )
    return Agent(
        agent_name=agent_name,
        agent_description=TOKEN_LAUNCH_AGENT_DESCRIPTION,
        system_prompt=full_system,
        model_name=model,
        tools=[launch_token, claim_fees],
        max_loops=1,
        output_type="final",
    )


# ---- Developer worker ----


def create_developer_agent(
    *,
    agent_name: str = DEVELOPER_AGENT_NAME,
    system_prompt: str | None = None,
    model_name: str | None = None,
) -> Agent:
    """
    Create a specialized developer sub-agent that uses Claude Code for implementation,
    refactoring, debugging, and code explanation.

    Args:
        agent_name: Name for the agent instance.
        system_prompt: Override the default developer specialist prompt.
        model_name: Model to use; defaults to env AGENT_MODEL or "gpt-4o-mini".

    Returns:
        Agent configured with run_claude_developer (Claude Code) as its tool.

    Note:
        Requires Claude Code (claude-agent-sdk) and appropriate API access for the
        underlying run_claude_agent calls.
    """
    prompt = system_prompt or DEVELOPER_SYSTEM_PROMPT
    full_system = build_agent_system_prompt(
        name=agent_name,
        description=DEVELOPER_AGENT_DESCRIPTION,
        system_prompt=prompt,
    )
    model = (
        model_name
        or os.environ.get("AGENT_MODEL", "gpt-4o-mini").strip()
        or "gpt-4o-mini"
    )
    return Agent(
        agent_name=agent_name,
        agent_description=DEVELOPER_AGENT_DESCRIPTION,
        system_prompt=full_system,
        model_name=model,
        tools=[_run_claude_developer],
        max_loops=5,
        output_type="final",
    )
