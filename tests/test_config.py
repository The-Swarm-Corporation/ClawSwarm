from __future__ import annotations

from claw_swarm.config import load_agent_config


def test_load_agent_config_from_path(tmp_path):
    cfg = tmp_path / "claw_swarm.toml"
    cfg.write_text(
        """
[agent]
name = "ConfiguredBot"
description = "Configured description"
system_prompt = "Custom system"
model = "gpt-4o"
max_tokens = 4096
temperature = 0.3
""".strip()
    )

    loaded = load_agent_config(str(cfg))

    assert loaded is not None
    assert loaded.name == "ConfiguredBot"
    assert loaded.description == "Configured description"
    assert loaded.system_prompt == "Custom system"
    assert loaded.model == "gpt-4o"
    assert loaded.max_tokens == 4096
    assert loaded.temperature == 0.3


def test_load_agent_config_returns_none_for_missing_path(tmp_path):
    missing = tmp_path / "missing.toml"
    loaded = load_agent_config(str(missing))
    assert loaded is None
