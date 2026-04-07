from __future__ import annotations

import os
from typing import Any, Optional


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


def resolve_llm(
    model_spec: str | None,
    *,
    default: str,
) -> tuple[Optional[str], Optional[Any]]:
    """
    Resolve a model spec to either a cloud model name string or a local
    LLM wrapper object.

    Specs with a recognised prefix are built into wrapper objects:
      ``vllm/<model>``         → VLLMWrapper  (local GPU via vLLM)
      ``vllm-server/<model>``  → VLLMServerWrapper  (HTTP vLLM server)
      ``hf/<model>``           → HuggingFaceWrapper  (local Transformers)

    All other specs are treated as cloud model names and returned as strings.

    Precedence (same as resolve_model):
      1. Explicit model_spec argument
      2. WORKER_MODEL_NAME env var
      3. AGENT_MODEL env var
      4. Provided default value

    Returns:
        ``(model_name, None)``  — for cloud model names (pass as model_name=)
        ``(None, llm_object)``  — for local wrappers (pass as llm=)
    """
    from claw_swarm.llm import build_llm, is_local_spec

    spec = resolve_model(model_spec, default=default)
    if is_local_spec(spec):
        return None, build_llm(spec)
    return spec, None
