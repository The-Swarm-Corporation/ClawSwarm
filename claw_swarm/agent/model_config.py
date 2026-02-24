from __future__ import annotations

import os


def resolve_model(model_name: str | None, *, default: str) -> str:
    """
    Resolve the model name for agents that support a shared worker override.

    Precedence:
      1. Explicit model_name argument (if provided and non-empty)
      2. WORKER_MODEL_NAME env var (if set and non-empty)
      3. AGENT_MODEL env var (if set and non-empty)
      4. Provided default value
    """
    if model_name and model_name.strip():
        return model_name.strip()

    worker_env = os.environ.get("WORKER_MODEL_NAME", "").strip()
    if worker_env:
        return worker_env

    agent_env = os.environ.get("AGENT_MODEL", "").strip()
    if agent_env:
        return agent_env

    return default

