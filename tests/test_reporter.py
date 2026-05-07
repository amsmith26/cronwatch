"""Tests for cronwatch.reporter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronwatch.reporter import JobSummary, Report, build_summary, generate_report
from cronwatch.tracker import JobTracker, RunRecord, RunStatus
from cronwatch.config import JobConfig


DT = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def job_cfg() -> JobConfig:
    return JobConfig(name="backup", schedule="0 2 * * *", grace_seconds=300)


@pytest.fixture()
def records() -> list[RunRecord]:
    r1 = RunRecord(job_name="backup", started_at=datetime(2024, 1, 15, 2, 0, tzinfo=timezone.utc))
    r1.status = RunStatus.SUCCESS
    r1.duration_seconds = 30.0

    r2 = RunRecord(job_name="backup", started_at=datetime(2024, 1, 14, 2, 0, tzinfo=timezone.utc))
    r2.status = RunStatus.FAILURE
    r2.duration_seconds = 5.0

    r3 = RunRecord(job_name="backup", started_at=datetime(2024, 1, 13, 2, 0, tzinfo=timezone.utc))
    r3.status = RunStatus.MISSED

    return [r1, r2, r3]


def test_build_summary_counts(records):
    s = build_summary("backup", records)
    assert s.total_runs == 3
    assert s.successful_runs == 1
    assert s.failed_runs == 1
    assert s.missed_runs == 1


def test_build_summary_avg_duration(records):
    s = build_summary("backup", records)
    assert s.avg_duration_seconds == pytest.approx(17.5)


def test_build_summary_success_rate(records):
    s = build_summary("backup", records)
    assert s.success_rate == pytest.approx(100 / 3)


def test_build_summary_last_run(records):
    s = build_summary("backup", records)
    assert s.last_status == RunStatus.SUCCESS
    assert s.last_run_at == datetime(2024, 1, 15, 2, 0, tzinfo=timezone.utc)


def test_build_summary_empty():
    s = build_summary("noop", [])
    assert s.total_runs == 0
    assert s.success_rate is None
    assert s.avg_duration_seconds is None


def test_generate_report_includes_all_jobs(job_cfg, records):
    tracker = JobTracker([job_cfg])
    tracker.history["backup"] = records
    report = generate_report(tracker)
    assert "backup" in report.summaries


def test_report_as_text_contains_job_name(job_cfg, records):
    tracker = JobTracker([job_cfg])
    tracker.history["backup"] = records
    report = generate_report(tracker)
    text = report.as_text()
    assert "backup" in text
    assert "CronWatch Report" in text


def test_report_as_text_empty_tracker(job_cfg):
    tracker = JobTracker([job_cfg])
    report = generate_report(tracker)
    text = report.as_text()
    assert "No job data" in text
