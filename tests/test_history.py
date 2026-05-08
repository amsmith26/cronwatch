"""Tests for cronwatch.history persistence layer."""

import os
from datetime import datetime

import pytest

from cronwatch.history import init_db, load_records, save_record
from cronwatch.tracker import RunRecord, RunStatus


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "cronwatch_test.db")
    init_db(path)
    return path


def _make_record(job_name="backup", status=RunStatus.SUCCESS, exit_code=0,
                 started_offset=0, finished_offset=10):
    started = datetime(2024, 6, 1, 12, 0, started_offset)
    finished = datetime(2024, 6, 1, 12, 0, finished_offset)
    return RunRecord(
        job_name=job_name,
        started_at=started,
        finished_at=finished,
        exit_code=exit_code,
        status=status,
    )


def test_init_db_creates_file(tmp_path):
    path = str(tmp_path / "subdir" / "cw.db")
    init_db(path)
    assert os.path.exists(path)


def test_save_and_load_single_record(db_path):
    rec = _make_record()
    save_record(db_path, rec)
    results = load_records(db_path, "backup")
    assert len(results) == 1
    assert results[0].job_name == "backup"
    assert results[0].status == RunStatus.SUCCESS
    assert results[0].exit_code == 0


def test_load_returns_empty_for_unknown_job(db_path):
    assert load_records(db_path, "nonexistent") == []


def test_load_respects_limit(db_path):
    for i in range(10):
        save_record(db_path, _make_record(started_offset=i, finished_offset=i + 5))
    results = load_records(db_path, "backup", limit=3)
    assert len(results) == 3


def test_load_orders_newest_first(db_path):
    for i in range(5):
        save_record(db_path, _make_record(started_offset=i, finished_offset=i + 2))
    results = load_records(db_path, "backup")
    timestamps = [r.started_at for r in results]
    assert timestamps == sorted(timestamps, reverse=True)


def test_save_record_with_no_finished_at(db_path):
    rec = RunRecord(
        job_name="nightly",
        started_at=datetime(2024, 6, 1, 3, 0, 0),
        finished_at=None,
        exit_code=None,
        status=RunStatus.RUNNING,
    )
    save_record(db_path, rec)
    results = load_records(db_path, "nightly")
    assert len(results) == 1
    assert results[0].finished_at is None
    assert results[0].status == RunStatus.RUNNING


def test_save_failure_record(db_path):
    rec = _make_record(status=RunStatus.FAILURE, exit_code=1)
    save_record(db_path, rec)
    results = load_records(db_path, "backup")
    assert results[0].status == RunStatus.FAILURE
    assert results[0].exit_code == 1
