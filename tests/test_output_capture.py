"""Tests for cronwatch.output_capture."""
from __future__ import annotations

import sys
import pytest

from cronwatch.output_capture import capture_command, truncate_output
from cronwatch.job_output import OutputRecord
from datetime import datetime, timezone


def _dummy_record(**kw) -> OutputRecord:
    return OutputRecord(
        job_name="test",
        run_id="r1",
        stdout=kw.get("stdout", ""),
        stderr=kw.get("stderr", ""),
        exit_code=kw.get("exit_code", 0),
        captured_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
    )


def test_capture_success_returns_true() -> None:
    rec, ok = capture_command("test", "exit 0")
    assert ok is True
    assert rec.exit_code == 0


def test_capture_failure_returns_false() -> None:
    rec, ok = capture_command("test", "exit 1")
    assert ok is False
    assert rec.exit_code == 1


def test_capture_stdout_is_captured() -> None:
    rec, ok = capture_command("test", f"{sys.executable} -c \"print('hello')\"")
    assert ok is True
    assert "hello" in rec.stdout


def test_capture_stderr_is_captured() -> None:
    rec, _ = capture_command(
        "test",
        f"{sys.executable} -c \"import sys; sys.stderr.write('err\\n')\"",
    )
    assert "err" in rec.stderr


def test_capture_uses_provided_run_id() -> None:
    rec, _ = capture_command("test", "exit 0", run_id="fixed-id")
    assert rec.run_id == "fixed-id"


def test_capture_generates_run_id_when_none() -> None:
    rec, _ = capture_command("test", "exit 0")
    assert rec.run_id  # non-empty


def test_capture_timeout_returns_false() -> None:
    rec, ok = capture_command("test", "sleep 10", timeout=0.05)
    assert ok is False
    assert rec.exit_code is None
    assert "TimeoutExpired" in rec.stderr


def test_capture_job_name_preserved() -> None:
    rec, _ = capture_command("my-job", "exit 0")
    assert rec.job_name == "my-job"


def test_truncate_output_no_op_when_small() -> None:
    rec = _dummy_record(stdout="short", stderr="tiny")
    result = truncate_output(rec, max_bytes=1024)
    assert result.stdout == "short"
    assert result.stderr == "tiny"


def test_truncate_output_truncates_large_stdout() -> None:
    big = "x" * 200
    rec = _dummy_record(stdout=big)
    result = truncate_output(rec, max_bytes=100)
    assert len(result.stdout.encode()) <= 120  # truncation marker adds a bit
    assert "[truncated]" in result.stdout


def test_truncate_output_preserves_metadata() -> None:
    rec = _dummy_record(stdout="data", exit_code=42)
    result = truncate_output(rec, max_bytes=1024)
    assert result.exit_code == 42
    assert result.job_name == rec.job_name
    assert result.run_id == rec.run_id
