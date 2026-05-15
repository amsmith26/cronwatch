"""Run a shell command and capture its stdout/stderr into an OutputRecord."""
from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from typing import Optional

from cronwatch.job_output import OutputRecord


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def capture_command(
    job_name: str,
    command: str,
    timeout: Optional[float] = None,
    env: Optional[dict] = None,
    run_id: Optional[str] = None,
) -> tuple[OutputRecord, bool]:
    """Run *command* in a shell and return (OutputRecord, success)."""
    if run_id is None:
        run_id = str(uuid.uuid4())

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        record = OutputRecord(
            job_name=job_name,
            run_id=run_id,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            captured_at=_utcnow(),
        )
        return record, result.returncode == 0
    except subprocess.TimeoutExpired as exc:
        record = OutputRecord(
            job_name=job_name,
            run_id=run_id,
            stdout=exc.stdout or "",
            stderr=f"TimeoutExpired: command exceeded {timeout}s\n" + (exc.stderr or ""),
            exit_code=None,
            captured_at=_utcnow(),
        )
        return record, False
    except Exception as exc:  # noqa: BLE001
        record = OutputRecord(
            job_name=job_name,
            run_id=run_id,
            stdout="",
            stderr=f"Exception during capture: {exc}\n",
            exit_code=None,
            captured_at=_utcnow(),
        )
        return record, False


def truncate_output(record: OutputRecord, max_bytes: int = 65_536) -> OutputRecord:
    """Return a copy of *record* with stdout/stderr truncated to *max_bytes* each."""
    def _trunc(s: str) -> str:
        encoded = s.encode("utf-8", errors="replace")
        if len(encoded) <= max_bytes:
            return s
        return encoded[:max_bytes].decode("utf-8", errors="replace") + "\n[truncated]"

    return OutputRecord(
        job_name=record.job_name,
        run_id=record.run_id,
        stdout=_trunc(record.stdout),
        stderr=_trunc(record.stderr),
        exit_code=record.exit_code,
        captured_at=record.captured_at,
    )
