"""Lightweight file-based locking to prevent concurrent cron job runs."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


class JobLock:
    """File-based lock for a single job.

    The lock file contains the PID of the process that holds it.
    Stale locks (process no longer running) are automatically removed.
    """

    def __init__(self, job_name: str, lock_dir: str = "/tmp/cronwatch") -> None:
        self.job_name = job_name
        self._dir = Path(lock_dir)
        self._path = self._dir / f"{job_name}.lock"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_pid(self) -> Optional[int]:
        try:
            return int(self._path.read_text().strip())
        except (FileNotFoundError, ValueError):
            return None

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def _stale(self) -> bool:
        pid = self._read_pid()
        if pid is None:
            return True
        return not self._pid_alive(pid)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def acquire(self) -> None:
        """Acquire the lock or raise *LockError* if already held."""
        self._dir.mkdir(parents=True, exist_ok=True)
        if self._path.exists() and not self._stale():
            pid = self._read_pid()
            raise LockError(
                f"Job '{self.job_name}' is already running (PID {pid})"
            )
        # Write our PID (overwrites stale lock).
        self._path.write_text(str(os.getpid()))

    def release(self) -> None:
        """Release the lock.  No-op if the file is gone."""
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass

    def is_locked(self) -> bool:
        """Return True if the lock is held by a live process."""
        return self._path.exists() and not self._stale()

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "JobLock":
        self.acquire()
        return self

    def __exit__(self, *_) -> None:
        self.release()
