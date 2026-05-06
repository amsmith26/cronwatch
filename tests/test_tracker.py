"""Tests for cronwatch.tracker."""

import time

import pytest

from cronwatch.config import JobConfig
from cronwatch.tracker import JobTracker, RunStatus, TrackerRegistry


@pytest.fixture()
def job_config() -> JobConfig:
    return JobConfig(name="backup", schedule="0 2 * * *", grace_seconds=120)


@pytest.fixture()
def tracker(job_config: JobConfig) -> JobTracker:
    return JobTracker(config=job_config)


def test_record_start_creates_record(tracker: JobTracker) -> None:
    record = tracker.record_start()
    assert record.job_name == "backup"
    assert record.status == RunStatus.SUCCESS
    assert record.finished_at is None
    assert len(tracker.history) == 1


def test_record_finish_success(tracker: JobTracker) -> None:
    record = tracker.record_start()
    tracker.record_finish(record, exit_code=0)
    assert record.status == RunStatus.SUCCESS
    assert record.exit_code == 0
    assert record.finished_at is not None


def test_record_finish_failure(tracker: JobTracker) -> None:
    record = tracker.record_start()
    tracker.record_finish(record, exit_code=1)
    assert record.status == RunStatus.FAILURE
    assert "1" in record.message


def test_record_missed(tracker: JobTracker) -> None:
    ts = time.time() - 300
    record = tracker.record_missed(expected_at=ts)
    assert record.status == RunStatus.MISSED
    assert record.started_at == ts
    assert len(tracker.history) == 1


def test_last_run_returns_most_recent_completed(tracker: JobTracker) -> None:
    r1 = tracker.record_start(started_at=1000.0)
    tracker.record_finish(r1, exit_code=0, finished_at=1005.0)
    r2 = tracker.record_start(started_at=2000.0)
    tracker.record_finish(r2, exit_code=0, finished_at=2010.0)
    assert tracker.last_run() is r2


def test_last_run_none_when_no_completed(tracker: JobTracker) -> None:
    tracker.record_start()  # not finished
    assert tracker.last_run() is None


def test_failed_runs_filters_correctly(tracker: JobTracker) -> None:
    r1 = tracker.record_start()
    tracker.record_finish(r1, exit_code=0)
    r2 = tracker.record_start()
    tracker.record_finish(r2, exit_code=2)
    tracker.record_missed(expected_at=time.time())
    assert len(tracker.failed_runs()) == 2


def test_duration_computed(tracker: JobTracker) -> None:
    record = tracker.record_start(started_at=100.0)
    tracker.record_finish(record, exit_code=0, finished_at=115.0)
    assert record.duration == pytest.approx(15.0)


def test_registry_register_and_get(job_config: JobConfig) -> None:
    registry = TrackerRegistry()
    t = registry.register(job_config)
    assert registry.get("backup") is t
    assert registry.get("missing") is None


def test_registry_all(job_config: JobConfig) -> None:
    registry = TrackerRegistry()
    cfg2 = JobConfig(name="cleanup", schedule="*/5 * * * *")
    registry.register(job_config)
    registry.register(cfg2)
    assert len(registry.all()) == 2
