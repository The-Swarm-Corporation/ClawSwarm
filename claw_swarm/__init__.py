"""
ClawSwarm: Swarms-based agent with ClawSwarm prompt and Claude as a tool.
Responds on Telegram, Discord, and WhatsApp via the Messaging Gateway.
"""

from claw_swarm.agent import create_agent
from claw_swarm.tools import (
    run_claude_agent,
    run_claude_agent_async,
    stream_claude_agent,
)

__all__ = [
    "create_agent",
    "run_claude_agent",
    "run_claude_agent_async",
    "stream_claude_agent",
]
