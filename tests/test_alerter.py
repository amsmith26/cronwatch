"""Tests for cronwatch.alerter."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerter import (
    _build_body,
    _build_subject,
    dispatch_alert,
    send_email_alert,
)
from cronwatch.config import AlertConfig
from cronwatch.tracker import RunRecord, RunStatus


UTC = timezone.utc


@pytest.fixture()
def record() -> RunRecord:
    return RunRecord(
        job_name="backup",
        started_at=datetime(2024, 1, 15, 3, 0, 0, tzinfo=UTC),
        finished_at=datetime(2024, 1, 15, 3, 5, 0, tzinfo=UTC),
        status=RunStatus.FAILED,
        exit_code=1,
        output="Error: disk full",
    )


@pytest.fixture()
def alert_cfg() -> AlertConfig:
    return AlertConfig(
        email="ops@example.com",
        from_address="cronwatch@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
    )


def test_build_subject(record):
    subject = _build_subject(record, "Job failed")
    assert "backup" in subject
    assert "Job failed" in subject
    assert subject.startswith("[cronwatch]")


def test_build_body_contains_fields(record):
    body = _build_body(record, "Job failed")
    assert "backup" in body
    assert "Job failed" in body
    assert "1" in body          # exit_code
    assert "Error: disk full" in body


def test_send_email_no_recipient_returns_false(record):
    cfg = AlertConfig(email=None)
    result = send_email_alert(cfg, record, "Job failed")
    assert result is False


def test_send_email_calls_smtp(record, alert_cfg):
    mock_smtp = MagicMock()
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    result = send_email_alert(alert_cfg, record, "Job failed", smtp_factory=mock_smtp)

    assert result is True
    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    mock_smtp_instance.send_message.assert_called_once()


def test_send_email_returns_false_on_smtp_error(record, alert_cfg):
    def bad_smtp(host, port):
        raise smtplib.SMTPException("connection refused")

    result = send_email_alert(alert_cfg, record, "Job failed", smtp_factory=bad_smtp)
    assert result is False


def test_dispatch_alert_infers_reason_failed(record, alert_cfg):
    mock_smtp = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    dispatch_alert(alert_cfg, record, smtp_factory=mock_smtp)
    # Should not raise; reason inferred from FAILED status


def test_dispatch_alert_missed_reason(alert_cfg):
    missed = RunRecord(
        job_name="cleanup",
        started_at=datetime(2024, 1, 15, 4, 0, 0, tzinfo=UTC),
        status=RunStatus.MISSED,
    )
    mock_smtp = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=MagicMock())
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    dispatch_alert(alert_cfg, missed, smtp_factory=mock_smtp)
