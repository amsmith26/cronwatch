"""Tests for cronwatch.job_output (DB persistence layer)."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pathlib import Path

from cronwatch.job_output import (
    OutputRecord,
    init_output_db,
    save_output,
    load_output,
    load_recent_outputs,
)


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    p = str(tmp_path / "output.db")
    init_output_db(p)
    return p


def _make_record(job_name: str = "backup", run_id: str = "abc", **kw) -> OutputRecord:
    return OutputRecord(
        job_name=job_name,
        run_id=run_id,
        stdout=kw.get("stdout", "done\n"),
        stderr=kw.get("stderr", ""),
        exit_code=kw.get("exit_code", 0),
        captured_at=kw.get("captured_at", datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)),
    )


def test_init_db_creates_file(tmp_path: Path) -> None:
    p = str(tmp_path / "new.db")
    init_output_db(p)
    assert Path(p).exists()


def test_init_db_is_idempotent(db_path: str) -> None:
    init_output_db(db_path)  # second call must not raise


def test_save_and_load_roundtrip(db_path: str) -> None:
    rec = _make_record(stdout="hello", stderr="warn", exit_code=0)
    save_output(db_path, rec)
    loaded = load_output(db_path, rec.job_name, rec.run_id)
    assert loaded is not None
    assert loaded.stdout == "hello"
    assert loaded.stderr == "warn"
    assert loaded.exit_code == 0
    assert loaded.job_name == rec.job_name
    assert loaded.run_id == rec.run_id


def test_load_returns_none_for_unknown_run(db_path: str) -> None:
    result = load_output(db_path, "no-job", "no-run")
    assert result is None


def test_load_recent_outputs_returns_latest_first(db_path: str) -> None:
    for i in range(3):
        rec = _make_record(run_id=f"run-{i}", stdout=f"output {i}")
        save_output(db_path, rec)
    results = load_recent_outputs(db_path, "backup", limit=10)
    assert len(results) == 3
    # Most recent (highest id) should be first
    assert results[0].run_id == "run-2"


def test_load_recent_outputs_respects_limit(db_path: str) -> None:
    for i in range(5):
        save_output(db_path, _make_record(run_id=f"r{i}"))
    results = load_recent_outputs(db_path, "backup", limit=2)
    assert len(results) == 2


def test_load_recent_outputs_empty_for_unknown_job(db_path: str) -> None:
    assert load_recent_outputs(db_path, "ghost") == []


def test_has_output_true_when_stdout(db_path: str) -> None:
    rec = _make_record(stdout="something", stderr="")
    assert rec.has_output() is True


def test_has_output_false_when_both_empty(db_path: str) -> None:
    rec = _make_record(stdout="", stderr="")
    assert rec.has_output() is False


def test_combined_includes_both_streams() -> None:
    rec = _make_record(stdout="out\n", stderr="err\n")
    combined = rec.combined()
    assert "[stdout]" in combined
    assert "[stderr]" in combined
    assert "out" in combined
    assert "err" in combined


def test_combined_omits_empty_streams() -> None:
    rec = _make_record(stdout="only-out", stderr="")
    combined = rec.combined()
    assert "[stderr]" not in combined
    assert "only-out" in combined
