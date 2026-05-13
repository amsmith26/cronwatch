"""Tests for cronwatch.audit_log."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronwatch.audit_log import (
    AuditLog,
    EVENT_ALERT_SENT,
    EVENT_JOB_FINISHED,
    EVENT_JOB_MISSED,
    EVENT_JOB_STARTED,
)


@pytest.fixture()
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit" / "cronwatch.log"


@pytest.fixture()
def audit(log_path: Path) -> AuditLog:
    return AuditLog(log_path)


def test_write_creates_file(audit: AuditLog, log_path: Path) -> None:
    audit.write(EVENT_JOB_STARTED, "backup")
    assert log_path.exists()


def test_write_appends_json_line(audit: AuditLog, log_path: Path) -> None:
    audit.write(EVENT_JOB_STARTED, "backup")
    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == EVENT_JOB_STARTED
    assert entry["job"] == "backup"
    assert "ts" in entry


def test_write_with_detail(audit: AuditLog) -> None:
    audit.write(EVENT_ALERT_SENT, "cleanup", {"recipient": "ops@example.com"})
    entries = audit.read_all()
    assert entries[0]["recipient"] == "ops@example.com"


def test_multiple_writes_append(audit: AuditLog) -> None:
    audit.write(EVENT_JOB_STARTED, "job_a")
    audit.write(EVENT_JOB_FINISHED, "job_a", {"status": "success"})
    audit.write(EVENT_JOB_MISSED, "job_b")
    assert len(audit.read_all()) == 3


def test_read_all_empty_when_no_file(log_path: Path) -> None:
    audit = AuditLog(log_path)
    assert audit.read_all() == []


def test_read_for_job_filters_correctly(audit: AuditLog) -> None:
    audit.write(EVENT_JOB_STARTED, "alpha")
    audit.write(EVENT_JOB_STARTED, "beta")
    audit.write(EVENT_JOB_FINISHED, "alpha", {"status": "success"})
    result = audit.read_for_job("alpha")
    assert len(result) == 2
    assert all(e["job"] == "alpha" for e in result)


def test_tail_returns_last_n(audit: AuditLog) -> None:
    for i in range(10):
        audit.write(EVENT_JOB_STARTED, f"job_{i}")
    tail = audit.tail(3)
    assert len(tail) == 3
    assert tail[-1]["job"] == "job_9"


def test_tail_fewer_than_n(audit: AuditLog) -> None:
    audit.write(EVENT_JOB_STARTED, "only_one")
    tail = audit.tail(20)
    assert len(tail) == 1


def test_parent_dirs_created_automatically(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c" / "audit.log"
    log = AuditLog(deep)
    log.write(EVENT_JOB_STARTED, "x")
    assert deep.exists()
