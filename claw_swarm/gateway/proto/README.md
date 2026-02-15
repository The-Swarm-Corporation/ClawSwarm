# Messaging Gateway Proto

After editing `messaging_gateway.proto`, regenerate Python code from the repo root:

```bash
python -m grpc_tools.protoc -Iclaw_swarm/gateway/proto \
  --python_out=claw_swarm/gateway/proto \
  --grpc_python_out=claw_swarm/gateway/proto \
  claw_swarm/gateway/proto/messaging_gateway.proto
```

Then fix the import in `messaging_gateway_pb2_grpc.py` to be relative:

- Change `import messaging_gateway_pb2` to `from . import messaging_gateway_pb2`
