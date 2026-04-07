"""
Local LLM backends for ClawSwarm.

Supports three prefix schemes in model spec strings:

    vllm/<model>            — local vLLM engine (requires `pip install vllm`)
    vllm-server/<model>     — vLLM OpenAI-compatible HTTP server
    hf/<model>              — local HuggingFace Transformers pipeline
                              (requires `pip install transformers accelerate`)

Any spec without one of these prefixes is treated as a cloud model name
(OpenAI, Anthropic, etc.) and is returned unchanged by resolve_llm().

Usage
-----
    from claw_swarm.llm import build_llm

    wrapper = build_llm("vllm/mistralai/Mistral-7B-Instruct-v0.1")
    # wrapper.run("Hello") → str

Environment variables
---------------------
    VLLM_SERVER_URL        Base URL for vllm-server mode
                           (default: http://localhost:8000/v1)
    VLLM_TENSOR_PARALLEL   Number of GPUs for tensor parallelism (default: 1)
    VLLM_GPU_MEMORY        GPU memory fraction (default: 0.9)
    VLLM_MAX_MODEL_LEN     Max context length (default: None → model default)
    HF_DEVICE              Device for HF pipeline: cpu / cuda / mps
                           (default: auto)
"""

from __future__ import annotations

from claw_swarm.llm.vllm_wrapper import VLLMWrapper, VLLMServerWrapper
from claw_swarm.llm.hf_wrapper import HuggingFaceWrapper

_PREFIXES = ("vllm/", "vllm-server/", "hf/")


def is_local_spec(spec: str) -> bool:
    """Return True if *spec* refers to a local/self-hosted model."""
    return any(spec.startswith(p) for p in _PREFIXES)


def build_llm(
    spec: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 0.9,
) -> VLLMWrapper | VLLMServerWrapper | HuggingFaceWrapper:
    """
    Build and return a local LLM wrapper from a prefixed model spec string.

    Args:
        spec:        Prefixed model spec, e.g. "vllm/meta-llama/Llama-2-7b-chat-hf"
        temperature: Sampling temperature (default 0.7)
        max_tokens:  Max generated tokens (default 2048)
        top_p:       Top-p nucleus sampling (default 0.9)

    Returns:
        A wrapper object with a ``run(task: str) -> str`` method.

    Raises:
        ValueError: If the spec does not start with a recognised prefix.
    """
    import os

    if spec.startswith("vllm-server/"):
        model_name = spec[len("vllm-server/") :]
        base_url = os.environ.get(
            "VLLM_SERVER_URL", "http://localhost:8000/v1"
        )
        return VLLMServerWrapper(
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if spec.startswith("vllm/"):
        import os as _os

        model_name = spec[len("vllm/") :]
        return VLLMWrapper(
            model_name=model_name,
            tensor_parallel_size=int(
                _os.environ.get("VLLM_TENSOR_PARALLEL", "1")
            ),
            gpu_memory_utilization=float(
                _os.environ.get("VLLM_GPU_MEMORY", "0.9")
            ),
            max_model_len=_os.environ.get("VLLM_MAX_MODEL_LEN")
            and int(_os.environ["VLLM_MAX_MODEL_LEN"]),
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

    if spec.startswith("hf/"):
        model_name = spec[len("hf/") :]
        return HuggingFaceWrapper(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(
        f"build_llm: unrecognised prefix in {spec!r}. "
        f"Expected one of: vllm/, vllm-server/, hf/"
    )


__all__ = [
    "VLLMWrapper",
    "VLLMServerWrapper",
    "HuggingFaceWrapper",
    "build_llm",
    "is_local_spec",
]
