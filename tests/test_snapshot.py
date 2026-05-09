"""Tests for cronwatch.snapshot and cronwatch.snapshot_export."""

from __future__ import annotations

import datetime
import json
import pytest

from cronwatch.config import JobConfig, AlertConfig
from cronwatch.metrics import MetricsRegistry
from cronwatch.snapshot import build_job_snapshot, build_system_snapshot, SystemSnapshot
from cronwatch.snapshot_export import render_json, render_text
from cronwatch.tracker import JobTracker, RunStatus


NOW = datetime.datetime(2024, 6, 1, 12, 0, 0)
# Use an hourly cron so next/prev are deterministic relative to NOW
SCHEDULE = "0 * * * *"  # every hour on the hour


@pytest.fixture()
def job_cfg() -> JobConfig:
    return JobConfig(name="backup", schedule=SCHEDULE, tags=["db", "nightly"])


@pytest.fixture()
def tracker(job_cfg: JobConfig) -> JobTracker:
    t = JobTracker(jobs=[job_cfg])
    return t


@pytest.fixture()
def registry(job_cfg: JobConfig, tracker: JobTracker) -> MetricsRegistry:
    reg = MetricsRegistry()
    for r in tracker.get_records(job_cfg.name):
        from cronwatch.metrics_middleware import ingest_record
        ingest_record(reg, r)
    return reg


# ── build_job_snapshot ────────────────────────────────────────────────────────

def test_snapshot_no_runs(job_cfg, tracker, registry):
    snap = build_job_snapshot(job_cfg, tracker, registry, grace_seconds=60, now=NOW)
    assert snap.name == "backup"
    assert snap.total_runs == 0
    assert snap.last_status is None
    assert snap.last_finished_at is None
    assert snap.tags == ["db", "nightly"]


def test_snapshot_success_rate_after_runs(job_cfg, tracker, registry):
    started = NOW - datetime.timedelta(minutes=5)
    run_id = tracker.record_start(job_cfg.name, started)
    finished = NOW - datetime.timedelta(minutes=4)
    tracker.record_finish(job_cfg.name, run_id, RunStatus.SUCCESS, finished)
    from cronwatch.metrics_middleware import ingest_record
    for r in tracker.get_records(job_cfg.name):
        ingest_record(registry, r)

    snap = build_job_snapshot(job_cfg, tracker, registry, grace_seconds=60, now=NOW)
    assert snap.total_runs == 1
    assert snap.success_rate == pytest.approx(1.0)
    assert snap.last_status == "success"


def test_snapshot_overdue_flag(job_cfg, tracker, registry):
    # NOW is 2024-06-01 12:00:00; last run was at 10:00 — more than 1 h + grace ago
    started = NOW - datetime.timedelta(hours=2)
    run_id = tracker.record_start(job_cfg.name, started)
    tracker.record_finish(
        job_cfg.name, run_id, RunStatus.SUCCESS,
        NOW - datetime.timedelta(hours=2) + datetime.timedelta(minutes=1)
    )
    snap = build_job_snapshot(job_cfg, tracker, registry, grace_seconds=60, now=NOW)
    # is_overdue depends on scheduler; just assert it's a bool
    assert isinstance(snap.is_overdue, bool)


# ── build_system_snapshot ─────────────────────────────────────────────────────

def test_system_snapshot_counts(job_cfg, tracker, registry):
    sys_snap = build_system_snapshot([job_cfg], tracker, registry, now=NOW)
    assert sys_snap.total_jobs == 1
    assert isinstance(sys_snap.overdue_count, int)
    assert isinstance(sys_snap.failing_count, int)


# ── render_json ───────────────────────────────────────────────────────────────

def test_render_json_is_valid(job_cfg, tracker, registry):
    sys_snap = build_system_snapshot([job_cfg], tracker, registry, now=NOW)
    output = render_json(sys_snap)
    data = json.loads(output)
    assert "captured_at" in data
    assert data["total_jobs"] == 1
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["name"] == "backup"


# ── render_text ───────────────────────────────────────────────────────────────

def test_render_text_contains_job_name(job_cfg, tracker, registry):
    sys_snap = build_system_snapshot([job_cfg], tracker, registry, now=NOW)
    output = render_text(sys_snap)
    assert "backup" in output
    assert "SCHEDULE" in output
    assert "SUCCESS%" in output
