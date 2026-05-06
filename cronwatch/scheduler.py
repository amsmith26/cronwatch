"""Cron schedule utilities — compute next/previous run times from cron expressions."""

from __future__ import annotations

import time
from typing import Optional

try:
    from croniter import croniter  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImportError("croniter is required: pip install croniter") from exc


def next_run(cron_expression: str, base: Optional[float] = None) -> float:
    """Return the next scheduled timestamp after *base* (defaults to now)."""
    base_time = base if base is not None else time.time()
    itr = croniter(cron_expression, base_time)
    return itr.get_next(float)


def prev_run(cron_expression: str, base: Optional[float] = None) -> float:
    """Return the most recent scheduled timestamp before *base* (defaults to now)."""
    base_time = base if base is not None else time.time()
    itr = croniter(cron_expression, base_time)
    return itr.get_prev(float)


def is_overdue(cron_expression: str, grace_seconds: int = 60, now: Optional[float] = None) -> bool:
    """Return True if the last expected run has passed its grace window without finishing."""
    current = now if now is not None else time.time()
    last_expected = prev_run(cron_expression, base=current)
    return current > last_expected + grace_seconds


def seconds_until_next(cron_expression: str, now: Optional[float] = None) -> float:
    """Return seconds remaining until the next scheduled run."""
    current = now if now is not None else time.time()
    return next_run(cron_expression, base=current) - current
