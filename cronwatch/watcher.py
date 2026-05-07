"""Watcher: ties together the scheduler, tracker, and alerter into a
periodic check loop that detects missed / overdue cron jobs."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from cronwatch.alerter import dispatch_alert
from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.scheduler import is_overdue
from cronwatch.tracker import JobTracker, RunStatus

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def check_job(
    job: JobConfig,
    tracker: JobTracker,
    alert_cfg,
    *,
    now: Optional[datetime] = None,
) -> bool:
    """Check a single job for overdue / missed status.

    Returns True if an alert was dispatched.
    """
    now = now or _utcnow()

    if not is_overdue(job.schedule, job.grace_minutes, now=now):
        logger.debug("Job '%s' is not overdue.", job.name)
        return False

    last = tracker.last_record(job.name)

    # Already finished successfully inside the current window — no alert.
    if last is not None and last.status == RunStatus.SUCCESS:
        if last.finished_at and last.finished_at >= now.replace(
            second=0, microsecond=0
        ):
            logger.debug("Job '%s' finished successfully in current window.", job.name)
            return False

    # Determine alert reason.
    if last is None:
        reason = "Job has never run."
    elif last.status == RunStatus.FAILURE:
        reason = f"Last run failed (exit code {last.exit_code})."
    elif last.status == RunStatus.RUNNING:
        reason = "Job is still running past its expected completion time."
    else:
        reason = "Job did not run within the expected window."

    logger.warning("Overdue job detected: '%s' — %s", job.name, reason)
    dispatch_alert(last, alert_cfg, extra_context={"reason": reason, "job": job})
    return True


def run_watch_loop(
    config: CronwatchConfig,
    tracker: JobTracker,
    *,
    poll_interval: int = 60,
    run_once: bool = False,
) -> None:
    """Main watch loop.  Polls all configured jobs every *poll_interval* seconds."""
    logger.info(
        "cronwatch starting — monitoring %d job(s).", len(config.jobs)
    )
    while True:
        now = _utcnow()
        for job in config.jobs:
            try:
                check_job(job, tracker, config.alert)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Unexpected error while checking job '%s'.", job.name)

        if run_once:
            break

        logger.debug("Sleeping %d seconds until next poll.", poll_interval)
        time.sleep(poll_interval)
