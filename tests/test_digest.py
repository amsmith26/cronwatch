"""Tests for cronwatch.digest."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig, CronwatchConfig, JobConfig
from cronwatch.digest import (
    DigestResult,
    build_digest,
    collect_recent_records,
    send_digest,
)
from cronwatch.tracker import RunRecord, RunStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def job_cfg() -> JobConfig:
    return JobConfig(name="backup", schedule="0 2 * * *", grace_minutes=5)


@pytest.fixture()
def cfg(job_cfg: JobConfig) -> CronwatchConfig:
    return CronwatchConfig(jobs=[job_cfg])


@pytest.fixture()
def alert_cfg() -> AlertConfig:
    return AlertConfig(smtp_host="localhost", smtp_port=25, recipients=["ops@example.com"])


def _make_record(job_name: str, offset_hours: float = 0, status: RunStatus = RunStatus.SUCCESS) -> RunRecord:
    from datetime import timedelta
    started = datetime(2024, 6, 1, 11, 0, 0, tzinfo=timezone.utc) - timedelta(hours=offset_hours)
    finished = started.replace(minute=5)
    return RunRecord(
        job_name=job_name,
        started_at=started,
        finished_at=finished,
        exit_code=0 if status == RunStatus.SUCCESS else 1,
        status=status,
    )


# ---------------------------------------------------------------------------
# collect_recent_records
# ---------------------------------------------------------------------------

def test_collect_recent_records_filters_old(cfg, tmp_path):
    db = str(tmp_path / "cw.db")
    recent = _make_record("backup", offset_hours=1)
    old = _make_record("backup", offset_hours=30)

    with patch("cronwatch.digest.load_records", return_value=[recent, old]), \
         patch("cronwatch.digest._utcnow", return_value=_NOW):
        records = collect_recent_records(cfg, db, period_hours=24)

    assert recent in records
    assert old not in records


def test_collect_recent_records_empty_when_no_jobs(tmp_path):
    empty_cfg = CronwatchConfig(jobs=[])
    records = collect_recent_records(empty_cfg, str(tmp_path / "cw.db"), period_hours=24)
    assert records == []


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_build_digest_returns_none_when_no_records(cfg, tmp_path):
    db = str(tmp_path / "cw.db")
    with patch("cronwatch.digest.load_records", return_value=[]), \
         patch("cronwatch.digest._utcnow", return_value=_NOW):
        result = build_digest(cfg, db)
    assert result is None


def test_build_digest_returns_report_with_summaries(cfg, tmp_path):
    db = str(tmp_path / "cw.db")
    record = _make_record("backup")
    with patch("cronwatch.digest.load_records", return_value=[record]), \
         patch("cronwatch.digest._utcnow", return_value=_NOW):
        report = build_digest(cfg, db)

    assert report is not None
    assert len(report.summaries) == 1
    assert report.summaries[0].job_name == "backup"


# ---------------------------------------------------------------------------
# send_digest
# ---------------------------------------------------------------------------

def test_send_digest_returns_not_sent_when_no_records(cfg, alert_cfg, tmp_path):
    db = str(tmp_path / "cw.db")
    with patch("cronwatch.digest.load_records", return_value=[]), \
         patch("cronwatch.digest._utcnow", return_value=_NOW):
        result = send_digest(cfg, alert_cfg, db)

    assert isinstance(result, DigestResult)
    assert result.sent is False
    assert result.jobs_included == 0


def test_send_digest_calls_dispatch_when_records_exist(cfg, alert_cfg, tmp_path):
    db = str(tmp_path / "cw.db")
    record = _make_record("backup")
    with patch("cronwatch.digest.load_records", return_value=[record]), \
         patch("cronwatch.digest._utcnow", return_value=_NOW), \
         patch("cronwatch.digest.dispatch_alert", return_value=True) as mock_dispatch:
        result = send_digest(cfg, alert_cfg, db)

    mock_dispatch.assert_called_once()
    assert result.sent is True
    assert result.jobs_included == 1
