"""
Main agent loop: connect to the Messaging Gateway, poll for new messages,
run the ClawSwarm Swarms agent on each message, and send replies back via the replier.

The agent uses the ClawSwarm system prompt (see prompts/clawswarm.md) and Claude as a tool.
Runs 24/7 until interrupted (SIGINT/SIGTERM). Configure via environment variables.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Callable, Optional

from claw_swarm.agent import create_agent
from claw_swarm.gateway.proto import messaging_gateway_pb2 as pb
from claw_swarm.gateway.proto import messaging_gateway_pb2_grpc as pb_grpc
from claw_swarm.gateway.schema import UnifiedMessage
from claw_swarm.replier import send_message_async


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
    try:
        # Swarms Agent.run() is synchronous; run in thread to avoid blocking the async loop
        reply_text = await asyncio.to_thread(agent.run, task)
        if not reply_text or not str(reply_text).strip():
            reply_text = "I'm sorry, I couldn't generate a reply for that."
        else:
            reply_text = str(reply_text).strip()
    except Exception as e:
        reply_text = f"Sorry, something went wrong: {e!s}"
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
    import grpc

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
                    await _process_message(msg, agent=agent, on_reply=on_reply)
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    print(f"[agent] Gateway unavailable at {target}, retrying in {poll_interval_seconds}s...", file=sys.stderr)
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

    print("ClawSwarm agent started. Polling gateway for messages (Ctrl+C to stop).", file=sys.stderr)
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
