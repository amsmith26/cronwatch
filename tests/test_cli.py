"""Tests for cronwatch.cli."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.cli import main, _build_parser


MIN_YAML = """
jobs:
  - name: daily-backup
    schedule: "0 2 * * *"
    grace_seconds: 300
alerts:
  email_to: ""
"""


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    p = tmp_path / "cronwatch.yaml"
    p.write_text(MIN_YAML)
    return p


def test_no_command_returns_nonzero():
    assert main([]) == 1


def test_parser_watch_defaults():
    parser = _build_parser()
    args = parser.parse_args(["watch"])
    assert args.command == "watch"
    assert args.config == "cronwatch.yaml"
    assert args.interval == 60


def test_parser_report_defaults():
    parser = _build_parser()
    args = parser.parse_args(["report"])
    assert args.command == "report"
    assert args.config == "cronwatch.yaml"


def test_cmd_report_prints_output(config_file, capsys):
    rc = main(["report", "-c", str(config_file)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CronWatch Report" in out


def test_cmd_watch_keyboard_interrupt(config_file):
    with patch("cronwatch.cli.run_watch_loop", side_effect=KeyboardInterrupt):
        rc = main(["watch", "-c", str(config_file), "--interval", "1"])
    assert rc == 0


def test_cmd_watch_passes_interval(config_file):
    with patch("cronwatch.cli.run_watch_loop") as mock_loop:
        main(["watch", "-c", str(config_file), "--interval", "30"])
        _, kwargs = mock_loop.call_args
        assert kwargs.get("interval") == 30
