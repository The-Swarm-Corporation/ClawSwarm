"""
Unit tests for claw_swarm.agent_runner.
"""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from claw_swarm.agent_runner import (
    _extract_final_reply,
    _get_gateway_target,
    _process_message,
    run_agent_loop,
)
from claw_swarm.gateway.schema import Platform, UnifiedMessage


class TestExtractFinalReply:
    """Test _extract_final_reply."""

    def test_empty_input_returns_empty(self):
        assert _extract_final_reply("", "user msg") == ""
        assert _extract_final_reply("   \n  ", "user msg") == ""

    def test_marker_takes_after_last_marker(self):
        raw = "Preamble\n[Current message to answer]\nUser asked this\n\nReply here."
        assert (
            _extract_final_reply(raw, "User asked this")
            == "Reply here."
        )

    def test_marker_strips_echoed_user_message(self):
        raw = "[Current message to answer]\nWhat is 2+2?\n\nThe answer is 4."
        assert (
            _extract_final_reply(raw, "What is 2+2?")
            == "The answer is 4."
        )

    def test_clawswarm_label_extraction(self):
        raw = "Some context\n**ClawSwarm:** Hello, this is the reply."
        assert (
            _extract_final_reply(raw, "Hi")
            == "Hello, this is the reply."
        )

    def test_clawswarm_label_no_asterisks(self):
        raw = "Context\nClawSwarm: Here is my answer."
        assert _extract_final_reply(raw, "?") == "Here is my answer."

    def test_assistant_label_fallback(self):
        raw = "Chat\n**Assistant:** I am the assistant reply."
        assert (
            _extract_final_reply(raw, "x")
            == "I am the assistant reply."
        )

    def test_returns_last_content_block_without_label(self):
        raw = "Line one\n\nLine two\n\nLine three"
        result = _extract_final_reply(raw, "?")
        assert "Line three" in result

    def test_skips_trailing_context_headers(self):
        raw = "Answer: 42\n\n[Some context header]"
        result = _extract_final_reply(raw, "?")
        assert "42" in result

    def test_prefers_quoted_reply_over_runner_summary(self):
        raw = (
            "Director reply: “Hello! I’m ClawSwarm. How can I assist you today?”\n"
            "Loop 1 of 1 has been completed by ClawSwarm under the Director’s supervision."
        )
        result = _extract_final_reply(raw, "hello")
        assert "How can I assist you today" in result


class TestGetGatewayTarget:
    """Test _get_gateway_target."""

    def test_default_localhost_50051(self):
        with patch.dict(
            os.environ,
            {"GATEWAY_HOST": "", "GATEWAY_PORT": ""},
            clear=False,
        ):
            # Restore after so we don't break other tests
            try:
                if "GATEWAY_HOST" in os.environ:
                    del os.environ["GATEWAY_HOST"]
                if "GATEWAY_PORT" in os.environ:
                    del os.environ["GATEWAY_PORT"]
            except Exception:
                pass
        target = _get_gateway_target()
        assert "localhost" in target or "127" in target
        assert "50051" in target

    def test_custom_host_and_port(self):
        with patch.dict(
            os.environ,
            {
                "GATEWAY_HOST": "gate.example.com",
                "GATEWAY_PORT": "9000",
            },
        ):
            target = _get_gateway_target()
        assert target == "gate.example.com:9000"


class TestProcessMessage:
    """Test _process_message (async)."""

    @pytest.mark.asyncio
    async def test_empty_text_skips_processing(self):
        msg = UnifiedMessage(
            id="1",
            platform=Platform.TELEGRAM,
            channel_id="ch",
            sender_id="s",
            text="   ",
        )
        agent = MagicMock()
        with patch(
            "claw_swarm.agent_runner.send_message_async",
            new_callable=AsyncMock,
        ):
            with patch("claw_swarm.agent_runner.append_interaction"):
                await _process_message(msg, agent)
        agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_agent_and_sends_reply(
        self, mock_memory_path
    ):
        msg = UnifiedMessage(
            id="m1",
            platform=Platform.TELEGRAM,
            channel_id="ch1",
            sender_id="s1",
            text="Hello",
        )
        agent = MagicMock()
        agent.run.return_value = "**ClawSwarm:** Hi there!"
        send_mock = AsyncMock(return_value=(True, ""))
        with patch(
            "claw_swarm.agent_runner.send_message_async", send_mock
        ):
            with patch(
                "claw_swarm.agent_runner.read_memory", return_value=""
            ):
                with patch(
                    "claw_swarm.agent_runner.append_interaction"
                ):
                    with patch(
                        "claw_swarm.agent_runner.asyncio.to_thread",
                        new_callable=AsyncMock,
                    ) as to_thread:
                        to_thread.return_value = (
                            "**ClawSwarm:** Hi there!"
                        )
                        await _process_message(msg, agent)
        to_thread.assert_called_once()
        send_mock.assert_called_once()
        args = send_mock.call_args[0]
        assert args[0] == Platform.TELEGRAM
        assert args[1] == "ch1"
        assert "Hi there" in args[3]

    @pytest.mark.asyncio
    async def test_on_reply_callback_invoked(self):
        msg = UnifiedMessage(
            id="m1",
            platform=Platform.DISCORD,
            channel_id="ch",
            sender_id="s",
            text="Hey",
        )
        agent = MagicMock()
        with patch(
            "claw_swarm.agent_runner.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value="ClawSwarm: Reply",
        ):
            with patch(
                "claw_swarm.agent_runner.send_message_async",
                new_callable=AsyncMock,
                return_value=(True, ""),
            ):
                with patch(
                    "claw_swarm.agent_runner.append_interaction"
                ):
                    with patch(
                        "claw_swarm.agent_runner.read_memory",
                        return_value="",
                    ):
                        on_reply = AsyncMock()
                        await _process_message(
                            msg, agent, on_reply=on_reply
                        )
        on_reply.assert_called_once()
        assert on_reply.call_args[0][0] == msg
        assert "Reply" in on_reply.call_args[0][1]


class TestRunAgentLoop:
    """Test run_agent_loop (with mocks)."""

    @pytest.mark.asyncio
    async def test_loop_cancellable(self):
        stub = MagicMock()
        poll_resp = MagicMock()
        poll_resp.messages = []
        stub.PollMessages = AsyncMock(return_value=poll_resp)
        channel = MagicMock()
        channel.close = AsyncMock()
        with patch(
            "claw_swarm.agent_runner.grpc.aio.insecure_channel",
            return_value=channel,
        ):
            with patch(
                "claw_swarm.agent_runner.pb_grpc.MessagingGatewayStub",
                return_value=stub,
            ):
                task = asyncio.create_task(
                    run_agent_loop(
                        gateway_target="localhost:50051",
                        poll_interval_seconds=0.1,
                        agent=MagicMock(),
                    )
                )
                await asyncio.sleep(0.15)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
