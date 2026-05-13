"""Tests for cronwatch.cli_schedule."""

from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.cli_schedule import add_schedule_subparser, cmd_schedule

HOURLY = "0 * * * *"


class _FakeJob:
    def __init__(self, name: str, cron: str = HOURLY, grace_seconds: int = 0):
        self.name = name
        self.cron = cron
        self.grace_seconds = grace_seconds


def _make_cfg(*job_names):
    cfg = MagicMock()
    cfg.jobs = [_FakeJob(n) for n in job_names]
    return cfg


def _args(**kwargs):
    defaults = {"job": None, "overdue_only": False}
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    return ns


def test_add_schedule_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_schedule_subparser(subs)
    parsed = parser.parse_args(["schedule"])
    assert parsed.func is cmd_schedule


def test_cmd_schedule_no_jobs_prints_message(capsys):
    cfg = _make_cfg()
    rc = cmd_schedule(_args(), cfg)
    out = capsys.readouterr().out
    assert rc == 0
    assert "No matching" in out


def test_cmd_schedule_lists_jobs(capsys):
    cfg = _make_cfg("backup", "cleanup")
    rc = cmd_schedule(_args(), cfg)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "cleanup" in out


def test_cmd_schedule_filter_by_name(capsys):
    cfg = _make_cfg("backup", "cleanup")
    rc = cmd_schedule(_args(job="backup"), cfg)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "cleanup" not in out


def test_cmd_schedule_unknown_job_returns_1(capsys):
    cfg = _make_cfg("backup")
    rc = cmd_schedule(_args(job="nonexistent"), cfg)
    assert rc == 1


def test_cmd_schedule_overdue_only_no_overdue(capsys):
    cfg = _make_cfg("backup")
    with patch("cronwatch.job_schedule.is_overdue", return_value=False):
        rc = cmd_schedule(_args(overdue_only=True), cfg)
    out = capsys.readouterr().out
    assert "No matching" in out
    assert rc == 0


def test_cmd_schedule_returns_2_when_overdue(capsys):
    cfg = _make_cfg("backup")
    with patch("cronwatch.job_schedule.is_overdue", return_value=True):
        rc = cmd_schedule(_args(), cfg)
    assert rc == 2
