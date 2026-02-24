
## Configuration (`claw_config.yaml`)

`claw_config.yaml` lives at the project root and holds all non-secret configuration. Secrets (API keys, bot tokens) stay in `.env`.

Run the interactive wizard to create or overwrite it:

```bash
clawswarm onboarding          # create (skips if file already exists)
clawswarm onboarding --force  # overwrite existing file
```

The wizard walks through five sections with sensible defaults — just press **Enter** to accept them.

### Full structure and defaults

```yaml
agent:
  name: ClawSwarm                           # director agent display name
  description: A hierarchical swarm of agents that can handle complex tasks

worker:
  model_name: gpt-4o-mini                   # model used by all worker agents

gateway:
  host: "[::]"                              # gRPC bind address (all interfaces)
  port: 50051                               # gRPC port
  tls: false                                # set true to require TLS

api:
  port: 8080                                # HTTP API listen port (--api flag)
  key: ""                                   # leave blank for open access;
                                            # set to require X-API-Key header

runtime:
  verbose: false                            # verbose logging
```

### Config precedence

Values are resolved in this order (highest wins):

```
CLI flags  >  environment variables / .env  >  claw_config.yaml  >  built-in defaults
```

For example, `clawswarm run --gw-port 50052` overrides `gateway.port` in the YAML, which itself overrides the `GATEWAY_PORT` env var default.

### What goes where

| Setting | Where to put it |
|---------|----------------|
| Gateway host / port / TLS | `claw_config.yaml` → `gateway` |
| HTTP API port / auth key | `claw_config.yaml` → `api` |
| Agent name / description | `claw_config.yaml` → `agent` |
| Worker model name | `claw_config.yaml` → `worker` |
| Verbose mode | `claw_config.yaml` → `runtime` |
| OpenAI / Anthropic API keys | `.env` |
| Telegram / Discord / WhatsApp tokens | `.env` |
| TLS cert/key file paths | `.env` or environment |

---

## CLI Reference

```
clawswarm <command> [options]
```

### `clawswarm onboarding`

Create `claw_config.yaml` interactively.

```bash
clawswarm onboarding           # create (no-op if file exists)
clawswarm onboarding --force   # overwrite existing config
```

### `clawswarm run`

Start the gRPC gateway and swarm agent. Optionally add the HTTP API server.

```bash
clawswarm run                        # gateway + agent
clawswarm run --api                  # + HTTP API on configured port
clawswarm run --api --port 9000      # override HTTP API port
clawswarm run --gw-host 0.0.0.0      # override gateway bind host
clawswarm run --gw-port 50052        # override gateway port
clawswarm run --gw-tls               # enable TLS on the gateway
clawswarm run --api-key mysecret     # require X-API-Key on /v1/* requests
```

| Flag | Default | Description |
|------|---------|-------------|
| `--api` | off | Also start the FastAPI/uvicorn HTTP API server |
| `--port PORT` | `8080` | HTTP API listen port |
| `--gw-host HOST` | from config | gRPC gateway bind host |
| `--gw-port PORT` | from config | gRPC gateway port |
| `--gw-tls` | from config | Enable TLS on the gRPC gateway |
| `--api-key KEY` | from config | API auth key for all `/v1/*` endpoints |

### `clawswarm settings`

Show the current live configuration (merged from `claw_config.yaml`, `.env`, and environment). Secret values are masked.

```bash
clawswarm settings
```
