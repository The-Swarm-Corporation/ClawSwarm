"""
vLLM wrappers for ClawSwarm.

Two classes:
  VLLMWrapper       — wraps the local vLLM inference engine (requires GPU).
  VLLMServerWrapper — connects to a running vLLM OpenAI-compatible server.

vllm is imported lazily inside __init__ so that importing this module never
fails even when vllm is not installed.

Install:
    pip install vllm
"""

from __future__ import annotations

from typing import Optional


class VLLMWrapper:
    """
    Swarms-compatible wrapper for the local vLLM inference engine.

    Implements the ``run(task) -> str`` interface expected by
    ``swarms.Agent(llm=...)``.

    Args:
        model_name:             HuggingFace model ID or local path.
        tensor_parallel_size:   Number of GPUs for tensor parallelism.
        gpu_memory_utilization: Fraction of GPU VRAM to allocate (0–1).
        max_model_len:          Maximum sequence length; None = model default.
        temperature:            Sampling temperature.
        top_p:                  Top-p nucleus sampling.
        max_tokens:             Maximum tokens to generate per call.

    Example::

        wrapper = VLLMWrapper("mistralai/Mistral-7B-Instruct-v0.1")
        reply = wrapper.run("Explain PagedAttention in one paragraph.")
    """

    def __init__(
        self,
        model_name: str,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        max_model_len: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
    ) -> None:
        try:
            from vllm import LLM, SamplingParams
        except ImportError as exc:
            raise ImportError(
                "vllm is required for VLLMWrapper. "
                "Install it with: pip install vllm"
            ) from exc

        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        init_kwargs: dict = dict(
            model=model_name,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
        )
        if max_model_len is not None:
            init_kwargs["max_model_len"] = max_model_len

        print(
            f"[ClawSwarm] Loading vLLM model: {model_name} "
            f"(tensor_parallel={tensor_parallel_size})"
        )
        self._llm = LLM(**init_kwargs)
        self._SamplingParams = SamplingParams

    # ------------------------------------------------------------------
    # Swarms interface
    # ------------------------------------------------------------------

    def run(
        self,
        task: str,
        img: Optional[str] = None,  # noqa: ARG002 — kept for compat
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Run inference on *task* and return the generated text.

        Args:
            task:        The input prompt / task string.
            img:         Ignored (kept for Swarms interface compatibility).
            temperature: Override instance temperature for this call.
            top_p:       Override instance top_p for this call.
            max_tokens:  Override instance max_tokens for this call.

        Returns:
            Generated text as a plain string.
        """
        params = self._SamplingParams(
            temperature=(
                temperature
                if temperature is not None
                else self.temperature
            ),
            top_p=top_p if top_p is not None else self.top_p,
            max_tokens=(
                max_tokens
                if max_tokens is not None
                else self.max_tokens
            ),
        )
        outputs = self._llm.generate([task], params)
        return outputs[0].outputs[0].text

    def __call__(self, task: str, **kwargs) -> str:
        return self.run(task, **kwargs)

    def __repr__(self) -> str:
        return (
            f"VLLMWrapper(model={self.model_name!r}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens})"
        )


class VLLMServerWrapper:
    """
    Swarms-compatible wrapper for a vLLM OpenAI-compatible HTTP server.

    Use when vLLM is running as a separate process::

        python -m vllm.entrypoints.openai.api_server \\
            --model mistralai/Mistral-7B-Instruct-v0.1

    Then connect::

        wrapper = VLLMServerWrapper(
            base_url="http://localhost:8000/v1",
            model_name="mistralai/Mistral-7B-Instruct-v0.1",
        )

    Args:
        base_url:    Base URL of the running vLLM server (no trailing slash).
        model_name:  Model name as served by the server.
        api_key:     Optional API key (not usually required for local servers).
        temperature: Default sampling temperature.
        max_tokens:  Default max tokens to generate.
        timeout:     HTTP request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model_name: str = "default",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: float = 120.0,
    ) -> None:
        try:
            import httpx  # already a project dependency
        except ImportError as exc:
            raise ImportError(
                "httpx is required for VLLMServerWrapper. "
                "Install it with: pip install httpx"
            ) from exc

        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._headers: dict = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    # ------------------------------------------------------------------
    # Swarms interface
    # ------------------------------------------------------------------

    def run(
        self,
        task: str,
        img: Optional[str] = None,  # noqa: ARG002
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Send *task* to the vLLM server and return the generated text.

        Args:
            task:        The input prompt / task string.
            img:         Ignored (kept for Swarms interface compatibility).
            temperature: Override instance temperature for this call.
            max_tokens:  Override instance max_tokens for this call.

        Returns:
            Generated text as a plain string.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response from the server.
            httpx.RequestError:    On a network-level failure.
        """
        import httpx

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": task}],
            "temperature": (
                temperature
                if temperature is not None
                else self.temperature
            ),
            "max_tokens": (
                max_tokens
                if max_tokens is not None
                else self.max_tokens
            ),
        }
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=self._headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def __call__(self, task: str, **kwargs) -> str:
        return self.run(task, **kwargs)

    def __repr__(self) -> str:
        return (
            f"VLLMServerWrapper(url={self.base_url!r}, "
            f"model={self.model_name!r})"
        )
