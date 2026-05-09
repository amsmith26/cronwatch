"""Execute shell commands for cron jobs and record results in the tracker."""

import subprocess
import time
from datetime import datetime, timezone
from typing import Optional

from cronwatch.config import JobConfig
from cronwatch.tracker import JobTracker, RunStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_job(
    job: JobConfig,
    tracker: JobTracker,
    timeout: Optional[int] = None,
) -> bool:
    """Run *job.command* in a subprocess, record start/finish in *tracker*.

    Returns True if the command exited with code 0, False otherwise.
    """
    run_id = tracker.record_start(job.name)
    started_at = _utcnow()

    effective_timeout = timeout if timeout is not None else job.grace_period

    try:
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
        exit_code = result.returncode
        output = (result.stdout + result.stderr).strip()
        success = exit_code == 0
    except subprocess.TimeoutExpired:
        exit_code = -1
        output = f"Job timed out after {effective_timeout}s"
        success = False
    except Exception as exc:  # noqa: BLE001
        exit_code = -1
        output = f"Unexpected error: {exc}"
        success = False

    status = RunStatus.SUCCESS if success else RunStatus.FAILURE
    tracker.record_finish(run_id, status, exit_code=exit_code, output=output)
    return success


def run_jobs_sequential(
    jobs: list[JobConfig],
    tracker: JobTracker,
    timeout: Optional[int] = None,
) -> dict[str, bool]:
    """Run each job in *jobs* sequentially; return mapping of job name -> success."""
    results: dict[str, bool] = {}
    for job in jobs:
        results[job.name] = run_job(job, tracker, timeout=timeout)
    return results
