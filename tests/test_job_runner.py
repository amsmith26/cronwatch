"""Tests for cronwatch.job_runner."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import JobConfig
from cronwatch.job_runner import run_job, run_jobs_sequential
from cronwatch.tracker import JobTracker, RunStatus


@pytest.fixture()
def job_cfg():
    return JobConfig(
        name="test-job",
        command="echo hello",
        schedule="* * * * *",
        grace_period=60,
        tags=[],
    )


@pytest.fixture()
def tracker(job_cfg):
    t = JobTracker()
    t.register(job_cfg)
    return t


def test_run_job_success_returns_true(job_cfg, tracker):
    result = run_job(job_cfg, tracker)
    assert result is True


def test_run_job_success_records_success_status(job_cfg, tracker):
    run_job(job_cfg, tracker)
    records = tracker.get_records(job_cfg.name)
    assert len(records) == 1
    assert records[0].status == RunStatus.SUCCESS
    assert records[0].exit_code == 0


def test_run_job_failure_returns_false(job_cfg, tracker):
    job_cfg = JobConfig(
        name="fail-job",
        command="exit 1",
        schedule="* * * * *",
        grace_period=60,
        tags=[],
    )
    tracker.register(job_cfg)
    result = run_job(job_cfg, tracker)
    assert result is False


def test_run_job_failure_records_failure_status(tracker):
    failing = JobConfig(
        name="fail-job",
        command="exit 2",
        schedule="* * * * *",
        grace_period=60,
        tags=[],
    )
    tracker.register(failing)
    run_job(failing, tracker)
    records = tracker.get_records(failing.name)
    assert records[0].status == RunStatus.FAILURE
    assert records[0].exit_code == 2


def test_run_job_timeout_records_failure(job_cfg, tracker):
    slow = JobConfig(
        name="slow-job",
        command="sleep 10",
        schedule="* * * * *",
        grace_period=5,
        tags=[],
    )
    tracker.register(slow)
    result = run_job(slow, tracker, timeout=1)
    assert result is False
    records = tracker.get_records(slow.name)
    assert records[0].status == RunStatus.FAILURE
    assert "timed out" in (records[0].output or "")


def test_run_jobs_sequential_returns_all_results(tracker):
    jobs = [
        JobConfig(name="j1", command="echo a", schedule="* * * * *", grace_period=60, tags=[]),
        JobConfig(name="j2", command="exit 1", schedule="* * * * *", grace_period=60, tags=[]),
    ]
    for j in jobs:
        tracker.register(j)
    results = run_jobs_sequential(jobs, tracker)
    assert results["j1"] is True
    assert results["j2"] is False


def test_run_jobs_sequential_records_each_job(tracker):
    jobs = [
        JobConfig(name="ja", command="echo 1", schedule="* * * * *", grace_period=60, tags=[]),
        JobConfig(name="jb", command="echo 2", schedule="* * * * *", grace_period=60, tags=[]),
    ]
    for j in jobs:
        tracker.register(j)
    run_jobs_sequential(jobs, tracker)
    assert len(tracker.get_records("ja")) == 1
    assert len(tracker.get_records("jb")) == 1
