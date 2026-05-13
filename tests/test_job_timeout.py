"""Tests for cronwatch.job_timeout."""

from __future__ import annotations

import time
import pytest

from cronwatch.tracker import RunRecord, RunStatus
from cronwatch.job_timeout import (
    TimeoutResult,
    check_timeout,
    find_timed_out_jobs,
)


NOW = 1_700_000_000.0


def _running(job_name: str, started_at: float) -> RunRecord:
    rec = RunRecord(job_name=job_name, run_id="abc", status=RunStatus.RUNNING)
    rec.started_at = started_at
    return rec


def _finished(job_name: str, started_at: float) -> RunRecord:
    rec = RunRecord(job_name=job_name, run_id="abc", status=RunStatus.SUCCESS)
    rec.started_at = started_at
    return rec


# ---------------------------------------------------------------------------
# check_timeout
# ---------------------------------------------------------------------------

def test_check_timeout_running_exceeds_limit():
    rec = _running("backup", NOW - 200)
    assert check_timeout(rec, max_runtime=60, now=NOW) is True


def test_check_timeout_running_within_limit():
    rec = _running("backup", NOW - 30)
    assert check_timeout(rec, max_runtime=60, now=NOW) is False


def test_check_timeout_not_running_returns_false():
    rec = _finished("backup", NOW - 200)
    assert check_timeout(rec, max_runtime=60, now=NOW) is False


def test_check_timeout_no_started_at_returns_false():
    rec = RunRecord(job_name="backup", run_id="x", status=RunStatus.RUNNING)
    # started_at not set
    assert check_timeout(rec, max_runtime=60, now=NOW) is False


# ---------------------------------------------------------------------------
# find_timed_out_jobs
# ---------------------------------------------------------------------------

def test_find_timed_out_jobs_returns_timed_out():
    records = [
        _running("backup", NOW - 200),
        _running("sync", NOW - 10),
    ]
    limits = {"backup": 60, "sync": 60}
    results = find_timed_out_jobs(records, limits, now=NOW)
    assert len(results) == 1
    assert results[0].job_name == "backup"


def test_find_timed_out_jobs_no_limit_skipped():
    records = [_running("backup", NOW - 200)]
    results = find_timed_out_jobs(records, max_runtimes={}, now=NOW)
    assert results == []


def test_find_timed_out_jobs_elapsed_and_exceeded_by():
    records = [_running("job", NOW - 130)]
    results = find_timed_out_jobs(records, {"job": 60}, now=NOW)
    assert len(results) == 1
    r = results[0]
    assert abs(r.elapsed - 130) < 0.01
    assert abs(r.exceeded_by - 70) < 0.01


def test_find_timed_out_jobs_finished_job_excluded():
    records = [_finished("job", NOW - 200)]
    results = find_timed_out_jobs(records, {"job": 60}, now=NOW)
    assert results == []


def test_timeout_result_exceeded_by_zero_when_within():
    r = TimeoutResult(job_name="x", pid=None, started_at=NOW - 50, elapsed=50, max_runtime=60)
    assert r.exceeded_by == 0.0
