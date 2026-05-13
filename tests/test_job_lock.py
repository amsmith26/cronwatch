"""Tests for cronwatch.job_lock."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest

from cronwatch.job_lock import JobLock, LockError


@pytest.fixture()
def lock_dir(tmp_path: Path) -> str:
    return str(tmp_path / "locks")


@pytest.fixture()
def lock(lock_dir: str) -> JobLock:
    return JobLock("backup", lock_dir=lock_dir)


# ---------------------------------------------------------------------------
# Basic acquire / release
# ---------------------------------------------------------------------------

def test_acquire_creates_lock_file(lock: JobLock, lock_dir: str) -> None:
    lock.acquire()
    assert (Path(lock_dir) / "backup.lock").exists()
    lock.release()


def test_release_removes_lock_file(lock: JobLock, lock_dir: str) -> None:
    lock.acquire()
    lock.release()
    assert not (Path(lock_dir) / "backup.lock").exists()


def test_lock_file_contains_current_pid(lock: JobLock, lock_dir: str) -> None:
    lock.acquire()
    pid = int((Path(lock_dir) / "backup.lock").read_text().strip())
    assert pid == os.getpid()
    lock.release()


# ---------------------------------------------------------------------------
# Double-acquire
# ---------------------------------------------------------------------------

def test_double_acquire_raises_lock_error(lock: JobLock) -> None:
    lock.acquire()
    with pytest.raises(LockError, match="already running"):
        lock.acquire()
    lock.release()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

def test_context_manager_releases_on_exit(lock: JobLock, lock_dir: str) -> None:
    with lock:
        assert lock.is_locked()
    assert not lock.is_locked()


def test_context_manager_releases_on_exception(lock: JobLock) -> None:
    try:
        with lock:
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert not lock.is_locked()


# ---------------------------------------------------------------------------
# Stale lock handling
# ---------------------------------------------------------------------------

def test_stale_lock_is_overwritten(lock: JobLock, lock_dir: str) -> None:
    # Write a PID that definitely does not exist.
    Path(lock_dir).mkdir(parents=True, exist_ok=True)
    (Path(lock_dir) / "backup.lock").write_text("999999999")
    # Should not raise — stale lock is removed.
    lock.acquire()
    assert lock.is_locked()
    lock.release()


# ---------------------------------------------------------------------------
# is_locked
# ---------------------------------------------------------------------------

def test_is_locked_false_before_acquire(lock: JobLock) -> None:
    assert not lock.is_locked()


def test_is_locked_true_while_held(lock: JobLock) -> None:
    lock.acquire()
    assert lock.is_locked()
    lock.release()


# ---------------------------------------------------------------------------
# Independent locks per job
# ---------------------------------------------------------------------------

def test_different_jobs_have_independent_locks(lock_dir: str) -> None:
    a = JobLock("job_a", lock_dir=lock_dir)
    b = JobLock("job_b", lock_dir=lock_dir)
    a.acquire()
    b.acquire()  # must not raise
    assert a.is_locked()
    assert b.is_locked()
    a.release()
    b.release()
