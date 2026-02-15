"""
Unified message schema (Pydantic) for in-process use and adapter implementations.
Matches the gRPC UnifiedMessage / Platform definitions.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class Platform(IntEnum):
    UNSPECIFIED = 0
    TELEGRAM = 1
    DISCORD = 2
    WHATSAPP = 3


class UnifiedMessage(BaseModel):
    """Single message normalized from Telegram, Discord, or WhatsApp."""

    id: str
    platform: Platform
    channel_id: str
    thread_id: str = ""
    sender_id: str
    sender_handle: str = ""
    text: str = ""
    attachment_urls: list[str] = Field(default_factory=list)
    timestamp_utc_ms: int = 0
    raw_metadata: bytes = b""

    model_config = {"extra": "forbid"}

    def to_grpc(self) -> Any:
        """Convert to protobuf UnifiedMessage (caller imports messaging_gateway_pb2)."""
        from claw_swarm.gateway.proto import messaging_gateway_pb2 as pb

        return pb.UnifiedMessage(
            id=self.id,
            platform=int(self.platform),
            channel_id=self.channel_id,
            thread_id=self.thread_id or "",
            sender_id=self.sender_id,
            sender_handle=self.sender_handle or "",
            text=self.text or "",
            attachment_urls=self.attachment_urls,
            timestamp_utc_ms=self.timestamp_utc_ms,
            raw_metadata=self.raw_metadata or b"",
        )

    @classmethod
    def from_grpc(cls, msg: Any) -> UnifiedMessage:
        """Build from protobuf UnifiedMessage."""
        return cls(
            id=msg.id,
            platform=Platform(msg.platform),
            channel_id=msg.channel_id,
            thread_id=msg.thread_id or "",
            sender_id=msg.sender_id,
            sender_handle=msg.sender_handle or "",
            text=msg.text or "",
            attachment_urls=list(msg.attachment_urls),
            timestamp_utc_ms=msg.timestamp_utc_ms,
            raw_metadata=bytes(msg.raw_metadata),
        )
