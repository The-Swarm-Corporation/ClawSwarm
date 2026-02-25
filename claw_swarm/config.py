"""Configuration loading for optional ClawSwarm agent settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass(frozen=True)
class AgentConfig:
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


def _default_config_paths() -> list[Path]:
    return [
        Path(os.getcwd()) / "claw_swarm.toml",
        Path.home() / ".claw_swarm" / "config.toml",
    ]


def _coerce_int(value: object, key: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _coerce_float(value: object, key: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    return float(value)


def _coerce_str(value: object, key: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    cleaned = value.strip()
    return cleaned or None


def load_agent_config(config_path: str | None = None) -> AgentConfig | None:
    """Load optional agent configuration from TOML.

    Resolution order:
    1) explicit `config_path`
    2) `CLAWSWARM_CONFIG` env var
    3) `./claw_swarm.toml`
    4) `~/.claw_swarm/config.toml`
    """
    path_candidates: list[Path] = []
    if config_path:
        path_candidates.append(Path(config_path))
    env_path = os.environ.get("CLAWSWARM_CONFIG", "").strip()
    if env_path:
        path_candidates.append(Path(env_path))
    path_candidates.extend(_default_config_paths())

    resolved: Path | None = None
    for candidate in path_candidates:
        if candidate.is_file():
            resolved = candidate
            break
    if resolved is None:
        return None

    with resolved.open("rb") as f:
        raw = tomllib.load(f)

    agent = raw.get("agent", {})
    if not isinstance(agent, dict):
        raise ValueError("[agent] section must be a table")

    return AgentConfig(
        name=_coerce_str(agent.get("name"), "agent.name"),
        description=_coerce_str(
            agent.get("description"), "agent.description"
        ),
        system_prompt=_coerce_str(
            agent.get("system_prompt"), "agent.system_prompt"
        ),
        model=_coerce_str(agent.get("model"), "agent.model"),
        max_tokens=_coerce_int(
            agent.get("max_tokens"), "agent.max_tokens"
        ),
        temperature=_coerce_float(
            agent.get("temperature"), "agent.temperature"
        ),
    )
