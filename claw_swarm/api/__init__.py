"""
ClawSwarm HTTP API package.

Exposes the ClawSwarm hierarchical swarm agent as a public REST API
via FastAPI + uvicorn.  Start with:

    clawswarm api          # via CLI
    clawswarm-api          # via installed script
    python -m claw_swarm.api
"""

from claw_swarm.api.server import app, run

__all__ = ["app", "run"]
