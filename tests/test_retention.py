"""Tests for cronwatch.retention."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.history import init_db, save_record
from cronwatch.retention import prune_excess_records, prune_records
from cronwatch.tracker import RunRecord, RunStatus


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "test.db")
    init_db(p)
    return p


def _make_record(
    job: str = "myjob",
    started_offset: float = 0.0,
    status: RunStatus = RunStatus.SUCCESS,
) -> RunRecord:
    now = time.time() + started_offset
    return RunRecord(
        job_name=job,
        started_at=datetime.fromtimestamp(now, tz=timezone.utc),
        finished_at=datetime.fromtimestamp(now + 1, tz=timezone.utc),
        exit_code=0 if status == RunStatus.SUCCESS else 1,
        status=status,
    )


# ---------------------------------------------------------------------------
# prune_records
# ---------------------------------------------------------------------------

def test_prune_removes_old_records(db_path: str) -> None:
    old = _make_record(started_offset=-(40 * 86400))  # 40 days ago
    recent = _make_record(started_offset=-86400)       # 1 day ago
    save_record(db_path, old)
    save_record(db_path, recent)

    deleted = prune_records(db_path, older_than_days=30)

    assert deleted == 1


def test_prune_scoped_to_job(db_path: str) -> None:
    old_a = _make_record(job="job_a", started_offset=-(40 * 86400))
    old_b = _make_record(job="job_b", started_offset=-(40 * 86400))
    save_record(db_path, old_a)
    save_record(db_path, old_b)

    deleted = prune_records(db_path, job_name="job_a", older_than_days=30)

    assert deleted == 1


def test_prune_returns_zero_when_nothing_to_delete(db_path: str) -> None:
    recent = _make_record(started_offset=-3600)
    save_record(db_path, recent)

    deleted = prune_records(db_path, older_than_days=30)

    assert deleted == 0


def test_prune_invalid_days_raises(db_path: str) -> None:
    with pytest.raises(ValueError):
        prune_records(db_path, older_than_days=0)


# ---------------------------------------------------------------------------
# prune_excess_records
# ---------------------------------------------------------------------------

def test_prune_excess_keeps_most_recent(db_path: str) -> None:
    for i in range(10):
        save_record(db_path, _make_record(started_offset=float(-i * 60)))

    deleted = prune_excess_records(db_path, job_name="myjob", keep=5)

    assert deleted == 5


def test_prune_excess_no_op_when_under_limit(db_path: str) -> None:
    for i in range(3):
        save_record(db_path, _make_record(started_offset=float(-i * 60)))

    deleted = prune_excess_records(db_path, job_name="myjob", keep=10)

    assert deleted == 0


def test_prune_excess_invalid_keep_raises(db_path: str) -> None:
    with pytest.raises(ValueError):
        prune_excess_records(db_path, job_name="myjob", keep=0)
