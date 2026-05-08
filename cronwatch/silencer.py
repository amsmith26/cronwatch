"""Silence rules: suppress alerts for specific jobs during maintenance windows."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class SilenceRule:
    """A rule that suppresses alerts for a job pattern within a time window."""

    job_pattern: str  # fnmatch-style or exact job name
    start: datetime   # UTC
    end: datetime     # UTC
    reason: str = ""

    def matches_job(self, job_name: str) -> bool:
        import fnmatch
        return fnmatch.fnmatch(job_name, self.job_pattern)

    def is_active(self, at: Optional[datetime] = None) -> bool:
        now = at or datetime.now(timezone.utc)
        return self.start <= now <= self.end

    def suppresses(self, job_name: str, at: Optional[datetime] = None) -> bool:
        return self.matches_job(job_name) and self.is_active(at)


@dataclass
class Silencer:
    """Registry of silence rules; answers whether a job alert should be suppressed."""

    rules: List[SilenceRule] = field(default_factory=list)

    def add_rule(self, rule: SilenceRule) -> None:
        self.rules.append(rule)

    def is_silenced(self, job_name: str, at: Optional[datetime] = None) -> bool:
        """Return True if any active rule suppresses alerts for *job_name*."""
        return any(r.suppresses(job_name, at) for r in self.rules)

    def active_rules(self, at: Optional[datetime] = None) -> List[SilenceRule]:
        """Return all currently-active rules."""
        return [r for r in self.rules if r.is_active(at)]

    def expire_rules(self, at: Optional[datetime] = None) -> int:
        """Remove rules whose window has passed; return count removed."""
        now = at or datetime.now(timezone.utc)
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.end >= now]
        return before - len(self.rules)


def parse_silence_rules(raw: list) -> List[SilenceRule]:
    """Parse a list of dicts (e.g. from YAML) into SilenceRule objects."""
    rules: List[SilenceRule] = []
    for entry in raw or []:
        start = _parse_dt(entry["start"])
        end = _parse_dt(entry["end"])
        rules.append(SilenceRule(
            job_pattern=entry["job"],
            start=start,
            end=end,
            reason=entry.get("reason", ""),
        ))
    return rules


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 string, attaching UTC if no tzinfo present."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
