"""Tests for cronwatch.metrics."""
import pytest
from cronwatch.metrics import JobMetrics, MetricsRegistry


@pytest.fixture()
def reg() -> MetricsRegistry:
    return MetricsRegistry()


def test_record_success_increments_counts(reg):
    reg.record_success("backup", duration_seconds=5.0)
    m = reg.get("backup")
    assert m is not None
    assert m.total_runs == 1
    assert m.successful_runs == 1
    assert m.failed_runs == 0
    assert m.total_duration_seconds == 5.0


def test_record_failure_increments_counts(reg):
    reg.record_failure("backup", duration_seconds=2.5)
    m = reg.get("backup")
    assert m.total_runs == 1
    assert m.failed_runs == 1
    assert m.successful_runs == 0


def test_record_missed_increments_missed(reg):
    reg.record_missed("cleanup")
    m = reg.get("cleanup")
    assert m.missed_runs == 1
    assert m.total_runs == 0


def test_success_rate_zero_when_no_runs(reg):
    reg.record_missed("noop")
    m = reg.get("noop")
    assert m.success_rate == 0.0


def test_success_rate_correct(reg):
    reg.record_success("job", 1.0)
    reg.record_success("job", 1.0)
    reg.record_failure("job", 1.0)
    m = reg.get("job")
    assert abs(m.success_rate - 2 / 3) < 1e-9


def test_avg_duration_zero_when_no_successes(reg):
    reg.record_failure("job", 3.0)
    m = reg.get("job")
    assert m.avg_duration == 0.0


def test_avg_duration_correct(reg):
    reg.record_success("job", 4.0)
    reg.record_success("job", 6.0)
    m = reg.get("job")
    assert m.avg_duration == 5.0


def test_all_metrics_returns_all_jobs(reg):
    reg.record_success("a", 1.0)
    reg.record_success("b", 1.0)
    names = {m.job_name for m in reg.all_metrics()}
    assert names == {"a", "b"}


def test_reset_removes_job(reg):
    reg.record_success("tmp", 1.0)
    reg.reset("tmp")
    assert reg.get("tmp") is None


def test_get_unknown_job_returns_none(reg):
    assert reg.get("ghost") is None


def test_last_timestamps_set_on_success(reg):
    reg.record_success("ts_job", 1.0)
    m = reg.get("ts_job")
    assert m.last_run_ts is not None
    assert m.last_success_ts is not None
    assert m.last_failure_ts is None


def test_last_failure_ts_set_on_failure(reg):
    reg.record_failure("ts_job", 1.0)
    m = reg.get("ts_job")
    assert m.last_failure_ts is not None
    assert m.last_success_ts is None
