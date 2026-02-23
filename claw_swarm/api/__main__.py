"""Allow ``python -m claw_swarm.api`` to start the API server."""

import os

from dotenv import load_dotenv

load_dotenv()

from claw_swarm.api.server import run  # noqa: E402

if __name__ == "__main__":
    run()
