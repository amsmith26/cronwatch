"""Tests for cronwatch.job_checkpoint."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.job_checkpoint import (
    delete_checkpoint,
    init_checkpoint_db,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    path = str(tmp_path / "checkpoints.db")
    init_checkpoint_db(path)
    return path


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def test_init_creates_file(tmp_path: Path) -> None:
    path = str(tmp_path / "new.db")
    assert not os.path.exists(path)
    init_checkpoint_db(path)
    assert os.path.exists(path)


def test_init_is_idempotent(db_path: str) -> None:
    # Calling init a second time must not raise or corrupt data.
    save_checkpoint(db_path, "job_a", _dt("2024-01-01T12:00:00"))
    init_checkpoint_db(db_path)
    assert load_checkpoint(db_path, "job_a") is not None


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(db_path: str) -> None:
    ts = _dt("2024-06-15T08:30:00")
    save_checkpoint(db_path, "backup", ts)
    result = load_checkpoint(db_path, "backup")
    assert result is not None
    assert result.year == 2024
    assert result.month == 6
    assert result.day == 15


def test_load_unknown_job_returns_none(db_path: str) -> None:
    assert load_checkpoint(db_path, "does_not_exist") is None


def test_save_overwrites_previous_checkpoint(db_path: str) -> None:
    first = _dt("2024-01-01T00:00:00")
    second = _dt("2024-06-01T00:00:00")
    save_checkpoint(db_path, "job_x", first)
    save_checkpoint(db_path, "job_x", second)
    result = load_checkpoint(db_path, "job_x")
    assert result is not None
    assert result.month == 6


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_existing_checkpoint_returns_true(db_path: str) -> None:
    save_checkpoint(db_path, "job_del", _dt("2024-03-10T10:00:00"))
    assert delete_checkpoint(db_path, "job_del") is True
    assert load_checkpoint(db_path, "job_del") is None


def test_delete_nonexistent_returns_false(db_path: str) -> None:
    assert delete_checkpoint(db_path, "ghost") is False


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_returns_all_jobs(db_path: str) -> None:
    save_checkpoint(db_path, "alpha", _dt("2024-01-01T00:00:00"))
    save_checkpoint(db_path, "beta", _dt("2024-02-01T00:00:00"))
    mapping = list_checkpoints(db_path)
    assert set(mapping.keys()) == {"alpha", "beta"}


def test_list_empty_db_returns_empty_dict(db_path: str) -> None:
    assert list_checkpoints(db_path) == {}
