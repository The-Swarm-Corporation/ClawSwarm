"""
FastAPI HTTP server for direct public access to the ClawSwarm
hierarchical swarm agent.

Anyone can POST a task to this server and get a response from the
swarm without needing Telegram, Discord, or WhatsApp.

Endpoints
---------
GET  /                    Welcome + link map
GET  /health              Liveness check
POST /v1/run              Submit task (async) → returns job_id
POST /v1/run/sync         Submit task and wait → returns result
GET  /v1/jobs/{job_id}    Poll job status / fetch result
GET  /v1/jobs             List recent jobs

Authentication
--------------
Set ``API_KEY`` env var to require ``X-API-Key: <value>`` on all
/v1/* requests.  Leave unset for open access.

Public discovery
----------------
Binds to 0.0.0.0:API_PORT (default 8080).  On startup the server
fetches your machine's public IP and prints the full public URL:

    http://<public-ip>:<port>/docs

Forward / open that port in your router or firewall to share with
the world.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from claw_swarm.agent import create_agent, summarize_for_telegram
from claw_swarm.agent.memory import (
    append_interaction,
    read_memory,
)
from claw_swarm.agent.prompts import CLAWSWARM_SYSTEM
from claw_swarm.agent_runner import _extract_final_reply

console = Console()

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------


class JobRecord(BaseModel):
    """Serialisable record for a single swarm job."""

    job_id: str
    task: str
    status: str = "queued"
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    completed_at: Optional[str] = None


# job_id → JobRecord
_jobs: Dict[str, JobRecord] = {}

# job_id → asyncio.Event (signals completion; not stored in JobRecord)
_job_events: Dict[str, asyncio.Event] = {}

# Single FIFO queue processed by one background worker
_job_queue: asyncio.Queue[str] = asyncio.Queue()

# Shared agent instance (created once in the background worker)
_agent = None


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

_API_KEY = os.environ.get("API_KEY", "")


async def _verify_api_key(
    x_api_key: Optional[str] = Header(default=None),
) -> None:
    """Reject requests if API_KEY is set and the header doesn't match."""
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Missing or invalid X-API-Key header. "
                "Set X-API-Key: <your key> in the request."
            ),
        )


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    task: str = Field(
        ...,
        description=(
            "The task or question to send to the ClawSwarm "
            "hierarchical swarm agent."
        ),
        examples=["Search for the latest news on AI agents."],
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional key-value metadata stored with the job.",
    )


class RunResponse(BaseModel):
    job_id: str
    status: str
    poll_url: str


class SyncRunResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[str]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------


async def _worker() -> None:
    """
    Single background coroutine that drains _job_queue one job at a
    time so the agent instance is never called concurrently.
    """
    global _agent
    if _agent is None:
        _agent = create_agent()

    while True:
        job_id: str = await _job_queue.get()
        record = _jobs.get(job_id)
        if record is None:
            _job_queue.task_done()
            continue

        record.status = "running"
        task = record.task

        try:
            # Build the same context as agent_runner._process_message
            ctx = (
                "[Your system instructions - follow these]\n"
                f"{CLAWSWARM_SYSTEM.strip()}\n\n"
            )
            mem = read_memory()
            if mem:
                ctx += (
                    "[Previous conversation context from memory]\n"
                    f"{mem}\n\n"
                )
            ctx += f"[Current message to answer]\n{task}"

            # agent.run() is synchronous; run in thread pool
            raw = await asyncio.to_thread(_agent.run, ctx)
            raw_str = str(raw).strip() if raw else ""

            reply = await asyncio.to_thread(
                summarize_for_telegram, raw_str
            )
            if not reply:
                reply = _extract_final_reply(raw_str, task)
            if not reply:
                reply = (
                    "I'm sorry, I couldn't generate a reply "
                    "for that."
                )

            append_interaction(
                platform="API",
                channel_id="http",
                thread_id="",
                sender_handle="api_user",
                user_text=task,
                reply_text=reply,
                message_id=job_id,
            )

            record.status = "done"
            record.result = reply

        except Exception as exc:
            record.status = "failed"
            record.error = str(exc)

        finally:
            record.completed_at = datetime.now(
                timezone.utc
            ).isoformat()
            event = _job_events.get(job_id)
            if event is not None:
                event.set()
            _job_queue.task_done()


# ---------------------------------------------------------------------------
# Public IP helper
# ---------------------------------------------------------------------------


async def _get_public_ip() -> str:
    """Return this machine's public IPv4 address, or '<unknown>'."""
    for url in (
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
        "https://icanhazip.com",
    ):
        try:
            async with httpx.AsyncClient(timeout=4) as client:
                resp = await client.get(url)
                ip = resp.text.strip()
                if ip:
                    return ip
        except Exception:
            continue
    return "<unknown>"


def _api_port() -> int:
    return int(os.environ.get("API_PORT", "8080"))


# ---------------------------------------------------------------------------
# App lifespan (startup / shutdown)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _lifespan(app: FastAPI):
    worker_task = asyncio.create_task(_worker())
    port = _api_port()

    # Fetch public IP in background while worker starts
    public_ip = await _get_public_ip()

    local_url = f"http://localhost:{port}"
    public_url = f"http://{public_ip}:{port}"

    body = Text()
    body.append("ClawSwarm API is live!\n\n", style="bold green")
    body.append("  Local :  ", style="dim")
    body.append(f"{local_url}/docs\n", style="bold cyan")
    body.append("  Public:  ", style="dim")
    body.append(f"{public_url}/docs\n", style="bold yellow")
    body.append(
        "\n  Share the Public URL — anyone on the internet can\n"
        "  POST tasks to your swarm agent via that address.\n",
        style="dim",
    )
    if _API_KEY:
        body.append("\n  Auth:   ", style="dim")
        body.append("X-API-Key header required\n", style="bold red")
    else:
        body.append("\n  Auth:   ", style="dim")
        body.append(
            "Open (set API_KEY env var to lock it down)\n",
            style="dim yellow",
        )

    console.print(
        Panel(
            body,
            title="[bold white]ClawSwarm API[/bold white]",
            border_style="bright_green",
            padding=(0, 2),
        )
    )

    yield

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ClawSwarm API",
    description=(
        "Public REST API for the ClawSwarm hierarchical swarm agent. "
        "Submit any task and get a response powered by a director + "
        "specialist worker swarm (search, code, token launch, general "
        "reasoning)."
    ),
    version="0.0.8",
    lifespan=_lifespan,
    contact={
        "name": "The Swarm Corporation",
        "url": "https://github.com/The-Swarm-Corporation/ClawSwarm",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    port = _api_port()
    return JSONResponse(
        {
            "service": "ClawSwarm API",
            "docs": f"http://localhost:{port}/docs",
            "endpoints": {
                "completions": "POST /v1/agent/completions",
                "completions_sync": "POST /v1/agent/completions/sync",
                "job_status": "GET /v1/agent/jobs/{job_id}",
                "list_jobs": "GET /v1/agent/jobs",
            },
        }
    )


@app.get("/health", tags=["System"], summary="Liveness check")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "clawswarm-api"}


@app.post(
    "/v1/agent/completions",
    response_model=RunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Agent"],
    dependencies=[Depends(_verify_api_key)],
    summary="Submit a task (async)",
    description=(
        "Enqueue a task for the ClawSwarm hierarchical swarm agent. "
        "Returns a `job_id` immediately. Poll "
        "`GET /v1/agent/jobs/{job_id}` until `status` is `done` or "
        "`failed`."
    ),
)
async def submit_completion(body: RunRequest) -> RunResponse:
    job_id = str(uuid.uuid4())
    record = JobRecord(job_id=job_id, task=body.task)
    _jobs[job_id] = record
    _job_events[job_id] = asyncio.Event()
    await _job_queue.put(job_id)
    port = _api_port()
    return RunResponse(
        job_id=job_id,
        status="queued",
        poll_url=f"http://localhost:{port}/v1/agent/jobs/{job_id}",
    )


@app.post(
    "/v1/agent/completions/sync",
    response_model=SyncRunResponse,
    tags=["Agent"],
    dependencies=[Depends(_verify_api_key)],
    summary="Submit a task and wait for the result",
    description=(
        "Enqueue a task and block until the agent finishes (or until "
        "`timeout` seconds elapse, default 300). Ideal for quick "
        "one-shot queries. For long-running tasks, use "
        "`POST /v1/agent/completions` and poll the result."
    ),
)
async def submit_completion_sync(
    body: RunRequest,
    timeout: int = 300,
) -> SyncRunResponse:
    job_id = str(uuid.uuid4())
    record = JobRecord(job_id=job_id, task=body.task)
    done_event = asyncio.Event()
    _jobs[job_id] = record
    _job_events[job_id] = done_event
    await _job_queue.put(job_id)

    try:
        await asyncio.wait_for(
            done_event.wait(), timeout=float(timeout)
        )
    except asyncio.TimeoutError:
        return SyncRunResponse(
            job_id=job_id,
            status=record.status,
            result=None,
            error=(
                f"Timed out after {timeout}s. "
                f"Fetch GET /v1/agent/jobs/{job_id} to check later."
            ),
        )

    return SyncRunResponse(
        job_id=job_id,
        status=record.status,
        result=record.result,
        error=record.error,
    )


@app.get(
    "/v1/agent/jobs/{job_id}",
    response_model=JobRecord,
    tags=["Jobs"],
    dependencies=[Depends(_verify_api_key)],
    summary="Get job status / result",
)
async def get_job(job_id: str) -> JobRecord:
    record = _jobs.get(job_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )
    return record


@app.get(
    "/v1/agent/jobs",
    response_model=List[JobRecord],
    tags=["Jobs"],
    dependencies=[Depends(_verify_api_key)],
    summary="List recent jobs",
    description="Returns the most recent `limit` jobs (default 50).",
)
async def list_jobs(limit: int = 50) -> List[JobRecord]:
    all_jobs = list(_jobs.values())
    return all_jobs[-limit:]


# ---------------------------------------------------------------------------
# Module-level runner (used by the CLI entry point)
# ---------------------------------------------------------------------------


def run(host: str = "0.0.0.0", port: int | None = None) -> None:
    """
    Start the ClawSwarm API server with uvicorn.

    Binds to 0.0.0.0 so the server is reachable from outside the
    machine. Set ``API_PORT`` env var to change the port (default
    8080).
    """
    import uvicorn  # imported here so uvicorn is optional at import time

    if port is None:
        port = _api_port()

    uvicorn.run(
        "claw_swarm.api.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )
