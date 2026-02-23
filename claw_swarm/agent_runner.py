"""
Main agent loop: connect to the Messaging Gateway, poll for new messages,
run the ClawSwarm Swarms agent on each message, and send replies back via the replier.

The agent uses the ClawSwarm system prompt (claw_swarm.prompts) and Claude as a tool.
Runs 24/7 until interrupted (SIGINT/SIGTERM). Configure via environment variables.
"""

from __future__ import annotations

import asyncio
import grpc
import os
import signal
import sys
from typing import Callable, Optional

from claw_swarm.agent import create_agent, summarize_for_telegram
from claw_swarm.gateway.proto import messaging_gateway_pb2 as pb
from claw_swarm.agent.prompts import CLAWSWARM_SYSTEM
from claw_swarm.gateway.proto import (
    messaging_gateway_pb2_grpc as pb_grpc,
)
from claw_swarm.gateway.schema import UnifiedMessage
from claw_swarm.agent.memory import append_interaction, read_memory
from claw_swarm.replier import send_message_async


def _extract_final_reply(
    raw_output: str, current_user_message: str
) -> str:
    """
    Extract only the final agent reply from the agent output.

    The Swarms agent (or LLM) may return the full conversation, echoed context,
    and "[Current message to answer]" blocks. We want only the last reply to send
    to Telegram/Discord/WhatsApp.
    """
    if not raw_output or not raw_output.strip():
        return raw_output or ""
    text = raw_output.strip()
    marker = "[Current message to answer]"
    if marker in text:
        # Take everything after the last occurrence of the marker
        idx = text.rfind(marker)
        after_marker = text[idx + len(marker) :].strip()
        # Strip optional newline after marker, then optional echoed user message
        after_marker = after_marker.lstrip("\n").strip()
        task_stripped = (current_user_message or "").strip()
        if task_stripped and after_marker.startswith(task_stripped):
            remainder = (
                after_marker[len(task_stripped) :]
                .strip()
                .lstrip("\n")
            )
            if remainder:
                return remainder.strip()
        return after_marker
    # No marker: try to take the last agent reply (ClawSwarm or legacy Assistant label)
    for label in (
        "**ClawSwarm:**",
        "ClawSwarm:",
        "**Assistant:**",
        "Assistant:",
    ):
        idx = text.rfind(label)
        if idx >= 0:
            reply = text[idx + len(label) :].strip()
            if reply:
                return reply
    # Fallback: last contiguous block of content (skip trailing context headers)
    lines = [ln.strip() for ln in text.split("\n")]
    i = len(lines) - 1
    while i >= 0 and not lines[i]:
        i -= 1
    if i < 0:
        return text
    j = i
    while (
        j >= 0
        and lines[j]
        and not (
            lines[j].startswith("[") and "context" in lines[j].lower()
        )
    ):
        j -= 1
    return "\n".join(lines[j + 1 : i + 1]).strip() or text


def _get_gateway_target() -> str:
    host = os.environ.get("GATEWAY_HOST", "localhost")
    port = os.environ.get("GATEWAY_PORT", "50051")
    # gRPC target: "host:port" (for insecure); use "dns:///host:port" if needed
    if ":" in host and not host.startswith("["):
        # IPv6 or hostname:port
        return f"{host}:{port}" if port not in host else host
    return f"{host}:{port}"


async def _process_message(
    msg: UnifiedMessage,
    agent,
    on_reply: Optional[Callable[[UnifiedMessage, str], None]] = None,
) -> None:
    """Run the ClawSwarm Swarms agent on the message text and send the reply back."""
    task = msg.text.strip() if msg.text else "(no text)"
    if not task:
        return
    # 1. System prompt first so the agent always has identity and instructions.
    # 2. Then memory (past conversations) so it doesn't override or confuse the system.
    # 3. Then the current message to answer.
    task_with_context = (
        "[Your system instructions - follow these]\n"
        f"{CLAWSWARM_SYSTEM.strip()}\n\n"
    )
    memory_content = read_memory()
    if memory_content:
        task_with_context += (
            "[Previous conversation context from memory]\n"
            f"{memory_content}\n\n"
        )
    task_with_context += f"[Current message to answer]\n{task}"
    try:
        # Swarms agent (hierarchical swarm) .run() is synchronous; run in thread
        raw_output = await asyncio.to_thread(
            agent.run, task_with_context
        )
        raw_str = str(raw_output).strip() if raw_output else ""
        # Summarize swarm output for Telegram (concise, no emojis)
        reply_text = await asyncio.to_thread(
            summarize_for_telegram, raw_str
        )
        if not reply_text:
            reply_text = _extract_final_reply(raw_str, task)
        if not reply_text:
            reply_text = (
                "I'm sorry, I couldn't generate a reply for that."
            )
    except Exception as e:
        reply_text = f"Sorry, something went wrong: {e!s}"
    # Persist this interaction to memory (project root markdown file)
    append_interaction(
        platform=msg.platform.name,
        channel_id=msg.channel_id,
        thread_id=msg.thread_id or "",
        sender_handle=msg.sender_handle or "",
        user_text=task,
        reply_text=reply_text,
        message_id=msg.id,
    )
    # Send back to the same channel/thread
    ok, err = await send_message_async(
        platform=msg.platform,
        channel_id=msg.channel_id,
        thread_id=msg.thread_id or "",
        text=reply_text,
    )
    if not ok:
        print(f"[agent] Failed to send reply: {err}", file=sys.stderr)
    if on_reply:
        on_reply(msg, reply_text)


async def run_agent_loop(
    *,
    agent=None,
    poll_interval_seconds: float = 5.0,
    max_messages_per_poll: int = 20,
    gateway_target: str | None = None,
    on_message: Optional[Callable[[UnifiedMessage], None]] = None,
    on_reply: Optional[Callable[[UnifiedMessage, str], None]] = None,
) -> None:
    """
    Run the main agent loop: poll gateway for messages, process each with the ClawSwarm agent, send replies.

    Uses the Swarms agent from create_agent() (ClawSwarm prompt + Claude as tool). Runs until the task
    is cancelled (e.g. SIGINT/SIGTERM). Uses insecure gRPC by default.
    """
    if agent is None:
        agent = create_agent()
    target = gateway_target or _get_gateway_target()

    channel = grpc.aio.insecure_channel(target)
    stub = pb_grpc.MessagingGatewayStub(channel)
    since_ms = 0

    try:
        while True:
            try:
                req = pb.PollMessagesRequest(
                    since_timestamp_utc_ms=since_ms,
                    max_messages=max_messages_per_poll,
                )
                resp = await stub.PollMessages(req)
                for m in resp.messages:
                    msg = UnifiedMessage.from_grpc(m)
                    if msg.timestamp_utc_ms > since_ms:
                        since_ms = msg.timestamp_utc_ms
                    if on_message:
                        on_message(msg)
                    await _process_message(
                        msg, agent=agent, on_reply=on_reply
                    )
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    print(
                        f"[agent] Gateway unavailable at {target}, retrying in {poll_interval_seconds}s...",
                        file=sys.stderr,
                    )
                else:
                    print(f"[agent] gRPC error: {e}", file=sys.stderr)
            except asyncio.CancelledError:
                break
            await asyncio.sleep(poll_interval_seconds)
    finally:
        await channel.close()


def main() -> int:
    """Entry point: run the agent loop 24/7 with signal handling."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(run_agent_loop())

    def shutdown():
        task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            # Windows
            break

    print(
        "ClawSwarm agent started. Polling gateway for messages (Ctrl+C to stop).",
        file=sys.stderr,
    )
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
