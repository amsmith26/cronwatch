"""Tests for cronwatch.job_filter."""

from __future__ import annotations

import datetime
import pytest

from cronwatch.config import JobConfig
from cronwatch.tracker import JobTracker, RunRecord, RunStatus
from cronwatch.job_filter import (
    jobs_by_name,
    jobs_never_run,
    jobs_overdue,
    jobs_with_last_status,
    jobs_matching,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NOW = datetime.datetime(2024, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
_FAR_PAST = _NOW - datetime.timedelta(hours=5)


@pytest.fixture()
def jobs() -> list[JobConfig]:
    return [
        JobConfig(name="backup", schedule="0 * * * *", grace_period=300),
        JobConfig(name="cleanup", schedule="0 2 * * *", grace_period=600),
        JobConfig(name="report", schedule="0 6 * * *", grace_period=300),
    ]


@pytest.fixture()
def tracker(jobs) -> JobTracker:
    t = JobTracker()
    # 'backup' has a successful recent run
    rec = RunRecord(job_name="backup", started_at=_NOW - datetime.timedelta(minutes=10))
    rec.status = RunStatus.SUCCESS
    rec.finished_at = _NOW - datetime.timedelta(minutes=9)
    t._records["backup"] = [rec]
    # 'cleanup' has a failed run far in the past
    rec2 = RunRecord(job_name="cleanup", started_at=_FAR_PAST)
    rec2.status = RunStatus.FAILURE
    rec2.finished_at = _FAR_PAST + datetime.timedelta(seconds=30)
    t._records["cleanup"] = [rec2]
    # 'report' has never run
    return t


# ---------------------------------------------------------------------------
# jobs_by_name
# ---------------------------------------------------------------------------

def test_jobs_by_name_case_insensitive(jobs):
    result = jobs_by_name(jobs, "BACKUP")
    assert len(result) == 1
    assert result[0].name == "backup"


def test_jobs_by_name_case_sensitive_no_match(jobs):
    result = jobs_by_name(jobs, "BACKUP", case_sensitive=True)
    assert result == []


def test_jobs_by_name_no_match(jobs):
    assert jobs_by_name(jobs, "nonexistent") == []


# ---------------------------------------------------------------------------
# jobs_never_run
# ---------------------------------------------------------------------------

def test_jobs_never_run(jobs, tracker):
    result = jobs_never_run(jobs, tracker)
    assert len(result) == 1
    assert result[0].name == "report"


# ---------------------------------------------------------------------------
# jobs_with_last_status
# ---------------------------------------------------------------------------

def test_jobs_with_last_status_success(jobs, tracker):
    result = jobs_with_last_status(jobs, tracker, RunStatus.SUCCESS)
    assert len(result) == 1
    assert result[0].name == "backup"


def test_jobs_with_last_status_failure(jobs, tracker):
    result = jobs_with_last_status(jobs, tracker, RunStatus.FAILURE)
    assert len(result) == 1
    assert result[0].name == "cleanup"


# ---------------------------------------------------------------------------
# jobs_matching
# ---------------------------------------------------------------------------

def test_jobs_matching_custom_predicate(jobs):
    result = jobs_matching(jobs, lambda j: j.grace_period == 300)
    names = {j.name for j in result}
    assert names == {"backup", "report"}


def test_jobs_matching_no_match(jobs):
    assert jobs_matching(jobs, lambda j: False) == []
