"""Tests for the 'prune' CLI sub-command."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cronwatch.cli_retention import add_prune_subparser, cmd_prune
from cronwatch.config import AlertConfig, CronwatchConfig, JobConfig
from cronwatch.history import init_db, save_record
from cronwatch.tracker import RunRecord, RunStatus


def _cfg(db_path: str) -> CronwatchConfig:
    job = JobConfig(name="testjob", schedule="* * * * *", command="echo hi")
    alert = AlertConfig()
    return CronwatchConfig(jobs=[job], alert=alert, db_path=db_path)


def _make_record(job: str = "testjob", offset: float = 0.0) -> RunRecord:
    t = time.time() + offset
    return RunRecord(
        job_name=job,
        started_at=datetime.fromtimestamp(t, tz=timezone.utc),
        finished_at=datetime.fromtimestamp(t + 1, tz=timezone.utc),
        exit_code=0,
        status=RunStatus.SUCCESS,
    )


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "cw.db")
    init_db(p)
    return p


def _args(
    days: int = 30,
    keep: int | None = None,
    job: str | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(days=days, keep=keep, job=job)


def test_add_prune_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command")
    add_prune_subparser(subs)
    ns = parser.parse_args(["prune", "--days", "7"])
    assert ns.days == 7


def test_cmd_prune_removes_old_records(db_path: str) -> None:
    save_record(db_path, _make_record(offset=-(40 * 86400)))
    save_record(db_path, _make_record(offset=-3600))

    rc = cmd_prune(_args(days=30), _cfg(db_path))

    assert rc == 0


def test_cmd_prune_no_db_path_returns_error() -> None:
    cfg = _cfg("")
    rc = cmd_prune(_args(), cfg)
    assert rc == 1


def test_cmd_prune_with_keep_caps_records(db_path: str) -> None:
    for i in range(8):
        save_record(db_path, _make_record(offset=float(-i * 60)))

    rc = cmd_prune(_args(days=30, keep=5), _cfg(db_path))

    assert rc == 0


def test_cmd_prune_invalid_days_returns_error(db_path: str) -> None:
    rc = cmd_prune(_args(days=0), _cfg(db_path))
    assert rc == 1
