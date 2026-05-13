"""Job priority levels and priority-based ordering utilities."""
from __future__ import annotations

from enum import IntEnum
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from cronwatch.config import JobConfig


class Priority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


_NAME_MAP = {
    "low": Priority.LOW,
    "normal": Priority.NORMAL,
    "high": Priority.HIGH,
    "critical": Priority.CRITICAL,
}


def parse_priority(value: object) -> Priority:
    """Return a Priority from a string or integer.  Defaults to NORMAL."""
    if value is None:
        return Priority.NORMAL
    if isinstance(value, int):
        try:
            return Priority(value)
        except ValueError:
            return Priority.NORMAL
    if isinstance(value, str):
        return _NAME_MAP.get(value.lower(), Priority.NORMAL)
    return Priority.NORMAL


def get_priority(job: "JobConfig") -> Priority:
    """Return the Priority for *job*, reading from job.extra if present."""
    extra = getattr(job, "extra", None) or {}
    return parse_priority(extra.get("priority"))


def sort_by_priority(
    jobs: List["JobConfig"],
    descending: bool = True,
) -> List["JobConfig"]:
    """Return *jobs* sorted by priority.  Highest first when *descending* is True."""
    return sorted(jobs, key=get_priority, reverse=descending)


def jobs_at_or_above(
    jobs: List["JobConfig"],
    threshold: Priority,
) -> List["JobConfig"]:
    """Return only jobs whose priority is >= *threshold*."""
    return [j for j in jobs if get_priority(j) >= threshold]
