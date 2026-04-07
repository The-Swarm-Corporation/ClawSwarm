"""
HuggingFace Transformers wrapper for ClawSwarm.

Runs any causal-LM model locally using the ``transformers`` text-generation
pipeline.  ``transformers`` and ``accelerate`` are imported lazily so this
module never fails at import time when they are not installed.

Install:
    pip install transformers accelerate

For GPU use, also install the appropriate torch build:
    pip install torch --index-url https://download.pytorch.org/whl/cu121
"""

from __future__ import annotations

import os
from typing import Optional


class HuggingFaceWrapper:
    """
    Swarms-compatible wrapper for HuggingFace text-generation models.

    Implements the ``run(task) -> str`` interface expected by
    ``swarms.Agent(llm=...)``.

    Args:
        model_name:   HuggingFace model ID (e.g. ``"microsoft/phi-2"``).
        temperature:  Sampling temperature (0 = greedy).
        max_tokens:   Maximum new tokens to generate.
        device:       Device override: ``"cpu"``, ``"cuda"``, ``"mps"``,
                      or ``"auto"`` (default — picks the best available).
        trust_remote_code: Pass ``trust_remote_code=True`` to the pipeline
                      (required for some models like Qwen, Falcon).
        torch_dtype:  ``"auto"`` (default), ``"float16"``, or ``"bfloat16"``.

    Example::

        wrapper = HuggingFaceWrapper("microsoft/phi-2", max_tokens=512)
        reply = wrapper.run("Write a Python function to reverse a string.")
    """

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        device: str = "auto",
        trust_remote_code: bool = False,
        torch_dtype: str = "auto",
    ) -> None:
        try:
            from transformers import pipeline
            import torch
        except ImportError as exc:
            raise ImportError(
                "transformers and accelerate are required for HuggingFaceWrapper. "
                "Install with: pip install transformers accelerate"
            ) from exc

        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Resolve device
        _device = os.environ.get("HF_DEVICE", device)
        if _device == "auto":
            if torch.cuda.is_available():
                _device = "cuda"
            elif (
                hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                _device = "mps"
            else:
                _device = "cpu"

        # Resolve dtype
        _dtype_map = {
            "auto": "auto",
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        _torch_dtype = _dtype_map.get(torch_dtype, "auto")

        print(
            f"[ClawSwarm] Loading HuggingFace model: {model_name} on {_device}"
        )
        self._pipe = pipeline(
            "text-generation",
            model=model_name,
            device=_device if _device != "cuda" else 0,
            torch_dtype=_torch_dtype,
            trust_remote_code=trust_remote_code,
        )

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
        Run the model on *task* and return generated text.

        Args:
            task:        Input prompt / task string.
            img:         Ignored (kept for Swarms interface compatibility).
            temperature: Override instance temperature for this call.
            max_tokens:  Override instance max_tokens for this call.

        Returns:
            Generated text as a plain string (input prompt stripped).
        """
        _temp = (
            temperature
            if temperature is not None
            else self.temperature
        )
        _max = (
            max_tokens if max_tokens is not None else self.max_tokens
        )

        gen_kwargs: dict = {
            "max_new_tokens": _max,
            "do_sample": _temp > 0,
            "return_full_text": False,
        }
        if _temp > 0:
            gen_kwargs["temperature"] = _temp

        outputs = self._pipe(task, **gen_kwargs)
        return outputs[0]["generated_text"]

    def __call__(self, task: str, **kwargs) -> str:
        return self.run(task, **kwargs)

    def __repr__(self) -> str:
        return (
            f"HuggingFaceWrapper(model={self.model_name!r}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens})"
        )
