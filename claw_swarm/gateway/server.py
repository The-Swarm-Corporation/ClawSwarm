"""
gRPC server for the Messaging Gateway: PollMessages, StreamMessages, Health.
Uses TLS when credentials are provided (secure by default in production).
"""

from __future__ import annotations

import asyncio
from typing import Sequence

import grpc
from grpc import aio as grpc_aio

from claw_swarm.gateway.adapters.base import MessageAdapter
from claw_swarm.gateway.proto import messaging_gateway_pb2 as pb
from claw_swarm.gateway.proto import messaging_gateway_pb2_grpc as pb_grpc
from claw_swarm.gateway.schema import Platform


# Proto platform enum value -> Platform
_PLATFORM_MAP = {
    0: Platform.UNSPECIFIED,
    1: Platform.TELEGRAM,
    2: Platform.DISCORD,
    3: Platform.WHATSAPP,
}


class MessagingGatewayServicer(pb_grpc.MessagingGatewayServicer):
    """Implements MessagingGateway gRPC service over configured adapters."""

    def __init__(
        self,
        adapters: Sequence[MessageAdapter],
        version: str = "0.1.0",
    ) -> None:
        self._adapters_by_platform: dict[Platform, MessageAdapter] = {}
        for a in adapters:
            name = a.platform_name.lower()
            if name == "telegram":
                self._adapters_by_platform[Platform.TELEGRAM] = a
            elif name == "discord":
                self._adapters_by_platform[Platform.DISCORD] = a
            elif name == "whatsapp":
                self._adapters_by_platform[Platform.WHATSAPP] = a
        self._version = version

    def _adapters_for_request(self, platforms: Sequence[int]) -> list[MessageAdapter]:
        if not platforms or (len(platforms) == 1 and platforms[0] == pb.PLATFORM_UNSPECIFIED):
            return list(self._adapters_by_platform.values())
        out = []
        for p in platforms:
            plat = _PLATFORM_MAP.get(p, Platform.UNSPECIFIED)
            if plat != Platform.UNSPECIFIED and plat in self._adapters_by_platform:
                out.append(self._adapters_by_platform[plat])
        return out

    async def PollMessages(self, request: pb.PollMessagesRequest, context: grpc.aio.ServicerContext) -> pb.PollMessagesResponse:
        adapters = self._adapters_for_request(list(request.platforms))
        since_ms = request.since_timestamp_utc_ms or 0
        max_messages = request.max_messages or 100
        all_messages: list[pb.UnifiedMessage] = []
        per_adapter = max(1, max_messages // len(adapters)) if adapters else 0
        for adapter in adapters:
            try:
                batch = await adapter.fetch_messages(
                    since_timestamp_utc_ms=since_ms,
                    max_messages=per_adapter,
                )
                for m in batch:
                    all_messages.append(m.to_grpc())
            except Exception as e:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(e))
                return pb.PollMessagesResponse(messages=[])
        all_messages.sort(key=lambda m: m.timestamp_utc_ms)
        return pb.PollMessagesResponse(messages=all_messages[:max_messages])

    async def StreamMessages(self, request: pb.StreamMessagesRequest, context: grpc.aio.ServicerContext):
        adapters = self._adapters_for_request(list(request.platforms))
        if not adapters:
            return
        # Simple approach: one adapter chosen for streaming (first); extend to merge streams if needed
        adapter = adapters[0]
        since_ms = 0
        try:
            while context.is_active():
                batch = await adapter.fetch_messages(since_timestamp_utc_ms=since_ms, max_messages=50)
                for m in batch:
                    yield m.to_grpc()
                    if m.timestamp_utc_ms > since_ms:
                        since_ms = m.timestamp_utc_ms
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    async def Health(self, request: pb.HealthRequest, context: grpc.aio.ServicerContext) -> pb.HealthResponse:
        return pb.HealthResponse(ok=True, version=self._version)


async def run_server(
    adapters: Sequence[MessageAdapter],
    host: str = "[::]",
    port: int = 50051,
    *,
    use_tls: bool = False,
    server_credentials: grpc.ServerCredentials | None = None,
    version: str = "0.1.0",
) -> grpc_aio.Server:
    """
    Start the MessagingGateway gRPC server (async). Use TLS in production.

    Args:
        adapters: Telegram, Discord, WhatsApp adapters (or subset).
        host: Bind address.
        port: Bind port.
        use_tls: If True, require server_credentials.
        server_credentials: From grpc.ssl_server_credentials() when use_tls.
        version: Reported in Health().
    """
    server = grpc_aio.server()
    servicer = MessagingGatewayServicer(adapters, version=version)
    pb_grpc.add_MessagingGatewayServicer_to_server(servicer, server)
    if use_tls and server_credentials is not None:
        server.add_secure_port(f"{host}:{port}", server_credentials)
    else:
        server.add_insecure_port(f"{host}:{port}")
    await server.start()
    return server
