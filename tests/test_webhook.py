"""Tests for cronwatch.webhook and cronwatch.webhook_config."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.tracker import RunRecord, RunStatus
from cronwatch.webhook import _build_payload, send_webhook
from cronwatch.webhook_config import WebhookConfig, parse_webhook_configs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def record() -> RunRecord:
    started = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    finished = datetime(2024, 1, 15, 10, 0, 45, tzinfo=timezone.utc)
    return RunRecord(
        job_name="backup",
        status=RunStatus.FAILURE,
        started_at=started,
        finished_at=finished,
        exit_code=1,
        error="disk full",
    )


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------

def test_build_payload_fields(record):
    payload = _build_payload("backup", record)
    assert payload["job"] == "backup"
    assert payload["status"] == "failure"
    assert payload["exit_code"] == 1
    assert payload["error"] == "disk full"
    assert payload["duration_seconds"] == pytest.approx(45.0)


def test_build_payload_no_finished_at():
    r = RunRecord(job_name="nightly", status=RunStatus.RUNNING)
    payload = _build_payload("nightly", r)
    assert payload["duration_seconds"] is None
    assert payload["finished_at"] is None


# ---------------------------------------------------------------------------
# send_webhook
# ---------------------------------------------------------------------------

def test_send_webhook_empty_url_returns_false(record):
    assert send_webhook("", "backup", record) is False


def test_send_webhook_success(record):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_webhook("https://example.com/hook", "backup", record)

    assert result is True


def test_send_webhook_http_error_returns_false(record):
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="https://example.com/hook", code=500, msg="Server Error", hdrs={}, fp=None
    )):
        result = send_webhook("https://example.com/hook", "backup", record)

    assert result is False


def test_send_webhook_includes_signature_header(record):
    captured = {}

    def fake_urlopen(req, timeout):
        captured["headers"] = dict(req.headers)
        mock_resp = MagicMock()
        mock_resp.status = 204
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        send_webhook("https://example.com/hook", "backup", record, secret="mysecret")

    assert "X-cronwatch-signature" in captured["headers"]
    assert captured["headers"]["X-cronwatch-signature"].startswith("sha256=")


# ---------------------------------------------------------------------------
# parse_webhook_configs
# ---------------------------------------------------------------------------

def test_parse_empty_returns_empty():
    assert parse_webhook_configs(None) == []
    assert parse_webhook_configs([]) == []


def test_parse_single_mapping():
    raw = {"url": "https://hooks.example.com/abc", "secret": "s3cr3t"}
    configs = parse_webhook_configs(raw)
    assert len(configs) == 1
    assert configs[0].url == "https://hooks.example.com/abc"
    assert configs[0].secret == "s3cr3t"


def test_parse_list_of_mappings():
    raw = [
        {"url": "https://a.example.com"},
        {"url": "https://b.example.com", "on_statuses": ["failure"]},
    ]
    configs = parse_webhook_configs(raw)
    assert len(configs) == 2
    assert configs[1].on_statuses == ["failure"]


def test_parse_missing_url_raises():
    with pytest.raises(ValueError, match="url"):
        parse_webhook_configs({"secret": "x"})


def test_wants_status():
    cfg = WebhookConfig(url="https://example.com", on_statuses=["failure"])
    assert cfg.wants_status("failure") is True
    assert cfg.wants_status("success") is False
