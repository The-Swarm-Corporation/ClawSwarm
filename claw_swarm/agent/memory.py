"""
Agent memory: persist interactions in a markdown file at project root so the agent
remembers context across apps (Telegram, Discord, WhatsApp) and restarts.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

# Project root: directory containing the claw_swarm package
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_FILENAME = os.environ.get(
    "AGENT_MEMORY_FILE", "agent_memory.md"
)
MEMORY_PATH = _PROJECT_ROOT / MEMORY_FILENAME

# Cap size so we don't send huge context every time (keep last ~100KB of content)
MAX_MEMORY_CHARS = int(
    os.environ.get("AGENT_MEMORY_MAX_CHARS", "100000")
)


def get_memory_path() -> Path:
    """Return the path to the agent memory file (in project root)."""
    return MEMORY_PATH


def read_memory() -> str:
    """
    Read the agent memory file. Returns empty string if missing or unreadable.
    Trims to last MAX_MEMORY_CHARS to keep context size bounded.
    """
    path = get_memory_path()
    try:
        if not path.exists():
            return ""
        raw = path.read_text(encoding="utf-8")
        if len(raw) <= MAX_MEMORY_CHARS:
            return raw.strip()
        return raw[-MAX_MEMORY_CHARS:].strip()
    except OSError:
        return ""


def append_interaction(
    platform: str,
    channel_id: str,
    thread_id: str,
    sender_handle: str,
    user_text: str,
    reply_text: str,
    message_id: str = "",
) -> None:
    """
    Append one user/agent exchange to the memory file (markdown).
    Creates the file if it does not exist.
    """
    path = get_memory_path()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    channel = channel_id
    if thread_id:
        channel = f"{channel_id} (thread {thread_id})"
    who = f"@{sender_handle}" if sender_handle else "user"
    block = f"""
## {ts}
- **Platform:** {platform}
- **Channel:** {channel}
- **{who}:** {_escape_block(user_text)}
- **ClawSwarm:** {_escape_block(reply_text)}
"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
    except OSError:
        pass  # avoid breaking the agent if disk is full or read-only


def _escape_block(s: str) -> str:
    """Escape markdown block so one-line display is safe; for multi-line we keep newlines."""
    if not s:
        return ""
    return s.replace("\r\n", "\n").strip()
