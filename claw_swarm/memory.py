"""
Backward-compatible shim for agent memory helpers.

Tests and older integrations import `claw_swarm.memory`, while the
implementation lives in `claw_swarm.agent.memory`.
"""

from __future__ import annotations

from claw_swarm.agent.memory import (  # noqa: F401
    MAX_MEMORY_CHARS,
    MEMORY_FILENAME,
    MEMORY_PATH,
    append_interaction,
    get_memory_path,
    read_memory,
)
