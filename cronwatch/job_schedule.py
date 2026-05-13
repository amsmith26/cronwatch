"""Utilities for parsing and describing job schedule metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.scheduler import next_run, prev_run, is_overdue, seconds_until_next


@dataclass
class ScheduleInfo:
    cron_expr: str
    grace_seconds: int
    next_run_ts: float
    prev_run_ts: float
    seconds_until_next: float
    overdue: bool

    def human_next(self) -> str:
        """Return a human-readable countdown to the next run."""
        secs = int(self.seconds_until_next)
        if secs <= 0:
            return "now"
        minutes, seconds = divmod(secs, 60)
        hours, minutes = divmod(minutes, 60)
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    def status_label(self) -> str:
        """Return a short status string for display."""
        if self.overdue:
            return "OVERDUE"
        return "OK"


def get_schedule_info(cron_expr: str, grace_seconds: int = 0) -> ScheduleInfo:
    """Build a ScheduleInfo snapshot for the given cron expression."""
    nxt = next_run(cron_expr)
    prv = prev_run(cron_expr)
    overdue = is_overdue(cron_expr, grace_seconds)
    secs = seconds_until_next(cron_expr)
    return ScheduleInfo(
        cron_expr=cron_expr,
        grace_seconds=grace_seconds,
        next_run_ts=nxt,
        prev_run_ts=prv,
        seconds_until_next=secs,
        overdue=overdue,
    )


def describe_schedule(cron_expr: str, grace_seconds: int = 0) -> str:
    """Return a one-line human-readable description of the schedule."""
    info = get_schedule_info(cron_expr, grace_seconds)
    return (
        f"cron='{info.cron_expr}'  "
        f"status={info.status_label()}  "
        f"next_in={info.human_next()}  "
        f"grace={info.grace_seconds}s"
    )


def schedules_for_config(jobs: list) -> dict[str, ScheduleInfo]:
    """Return a mapping of job name -> ScheduleInfo for a list of JobConfig objects."""
    result: dict[str, ScheduleInfo] = {}
    for job in jobs:
        grace = getattr(job, "grace_seconds", 0) or 0
        result[job.name] = get_schedule_info(job.cron, grace)
    return result
