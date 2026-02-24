"""
Unit tests for claw_swarm.cli.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

from claw_swarm import cli


class TestFindDotenvPath:
    """Test _find_dotenv_path."""

    def test_finds_dotenv_in_cwd(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            "os.path.abspath", lambda x: str(tmp_path)
        )
        monkeypatch.setattr("os.getcwd", lambda: str(tmp_path))
        monkeypatch.setattr(
            "os.path.isfile", lambda p: p == str(tmp_path / ".env")
        )
        result = cli._find_dotenv_path()
        assert result is not None
        assert result.endswith(".env")

    def test_returns_none_when_no_dotenv(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        # Ensure no .env in cwd or parents (tmp_path has no .env)
        def isfile(p):
            return False

        monkeypatch.setattr("os.path.isfile", isfile)
        result = cli._find_dotenv_path()
        assert result is None


class TestCmdSettings:
    """Test cmd_settings."""

    def test_returns_zero(self):
        assert (
            cli.cmd_settings(__import__("argparse").Namespace()) == 0
        )

    def test_prints_settings_keys(self, capsys):
        with patch.dict(
            os.environ,
            {"GATEWAY_HOST": "0.0.0.0", "GATEWAY_PORT": "50051"},
            clear=False,
        ):
            cli.cmd_settings(__import__("argparse").Namespace())
        out, _ = capsys.readouterr()
        assert "GATEWAY_HOST" in out
        assert "GATEWAY_PORT" in out
        assert "ClawSwarm" in out

    def test_masks_secret_values(self, capsys):
        with patch.dict(
            os.environ,
            {"TELEGRAM_BOT_TOKEN": "secret12345678"},
            clear=False,
        ):
            cli.cmd_settings(__import__("argparse").Namespace())
        out, _ = capsys.readouterr()
        assert "secret12345678" not in out
        assert "..." in out or "***" in out


class TestMain:
    """Test CLI main."""

    def test_help_returns_zero(self):
        with patch.object(sys, "argv", ["clawswarm", "--help"]):
            with pytest.raises(SystemExit) as exc:
                cli.main()
        assert exc.value.code == 0

    def test_no_args_prints_help_and_returns_zero(self, capsys):
        with patch.object(sys, "argv", ["clawswarm"]):
            code = cli.main()
        assert code == 0
        out, _ = capsys.readouterr()
        assert (
            "run" in out
            or "settings" in out
            or "usage" in out.lower()
        )

    def test_settings_subcommand_calls_cmd_settings(self):
        with patch.object(sys, "argv", ["clawswarm", "settings"]):
            with patch(
                "claw_swarm.cli.cmd_settings", return_value=42
            ) as m:
                code = cli.main()
        assert code == 42
        m.assert_called_once()

    def test_onboarding_subcommand_calls_cmd_onboarding(self):
        with patch.object(sys, "argv", ["clawswarm", "onboarding"]):
            with patch(
                "claw_swarm.cli.cmd_onboarding", return_value=7
            ) as m:
                code = cli.main()
        assert code == 7
        m.assert_called_once()
