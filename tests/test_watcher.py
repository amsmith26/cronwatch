"""Tests for cronwatch.watcher — check_job logic."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import JobConfig, AlertConfig
from cronwatch.tracker import JobTracker, RunRecord, RunStatus
from cronwatch.watcher import check_job


HOURLY = "0 * * * *"
GRACE = 5


@pytest.fixture()
def job() -> JobConfig:
    return JobConfig(name="backup", schedule=HOURLY, grace_minutes=GRACE)


@pytest.fixture()
def alert_cfg() -> AlertConfig:
    return AlertConfig(email="ops@example.com")


@pytest.fixture()
def tracker() -> JobTracker:
    return JobTracker()


def _past(minutes: int = 70) -> datetime:
    """Return a UTC datetime *minutes* ago."""
    return datetime.now(tz=timezone.utc) - timedelta(minutes=minutes)


def _now_overdue() -> datetime:
    """A 'now' that is 6 minutes past the top of the hour (past grace)."""
    base = datetime.now(tz=timezone.utc).replace(minute=6, second=0, microsecond=0)
    return base


@patch("cronwatch.watcher.is_overdue", return_value=False)
def test_no_alert_when_not_overdue(mock_overdue, job, tracker, alert_cfg):
    dispatched = check_job(job, tracker, alert_cfg)
    assert dispatched is False
    mock_overdue.assert_called_once()


@patch("cronwatch.watcher.dispatch_alert")
@patch("cronwatch.watcher.is_overdue", return_value=True)
def test_alert_dispatched_when_never_run(mock_overdue, mock_dispatch, job, tracker, alert_cfg):
    dispatched = check_job(job, tracker, alert_cfg)
    assert dispatched is True
    mock_dispatch.assert_called_once()


@patch("cronwatch.watcher.dispatch_alert")
@patch("cronwatch.watcher.is_overdue", return_value=True)
def test_alert_dispatched_on_failure(mock_overdue, mock_dispatch, job, tracker, alert_cfg):
    rec = RunRecord(job_name="backup", started_at=_past())
    rec.status = RunStatus.FAILURE
    rec.exit_code = 1
    tracker._records["backup"] = [rec]  # pylint: disable=protected-access

    dispatched = check_job(job, tracker, alert_cfg)
    assert dispatched is True
    call_kwargs = mock_dispatch.call_args
    assert call_kwargs is not None


@patch("cronwatch.watcher.dispatch_alert")
@patch("cronwatch.watcher.is_overdue", return_value=True)
def test_alert_dispatched_when_still_running(mock_overdue, mock_dispatch, job, tracker, alert_cfg):
    rec = RunRecord(job_name="backup", started_at=_past())
    rec.status = RunStatus.RUNNING
    tracker._records["backup"] = [rec]  # pylint: disable=protected-access

    dispatched = check_job(job, tracker, alert_cfg)
    assert dispatched is True


@patch("cronwatch.watcher.dispatch_alert")
@patch("cronwatch.watcher.is_overdue", return_value=True)
def test_no_alert_on_recent_success(mock_overdue, mock_dispatch, job, tracker, alert_cfg):
    now = datetime.now(tz=timezone.utc)
    rec = RunRecord(job_name="backup", started_at=now - timedelta(minutes=2))
    rec.status = RunStatus.SUCCESS
    rec.finished_at = now  # finished *after* the window boundary
    tracker._records["backup"] = [rec]  # pylint: disable=protected-access

    dispatched = check_job(job, tracker, alert_cfg, now=now)
    # finished_at == now so it's >= the truncated now — no alert expected
    assert dispatched is False
    mock_dispatch.assert_not_called()
