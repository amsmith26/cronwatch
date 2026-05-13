"""Parse quota configuration from YAML job entries."""

from __future__ import annotations

from typing import Any, Dict, Optional

from cronwatch.job_quota import JobQuota, QuotaRule


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


_UNIT_SECONDS: Dict[str, float] = {
    "second": 1,
    "seconds": 1,
    "minute": 60,
    "minutes": 60,
    "hour": 3600,
    "hours": 3600,
    "day": 86400,
    "days": 86400,
}


def parse_quota_rule(raw: Optional[Dict[str, Any]]) -> Optional[QuotaRule]:
    """Parse a quota dict into a QuotaRule, or return None if absent/invalid."""
    if not raw:
        return None
    max_runs = _int(raw.get("max_runs"), 0)
    if max_runs <= 0:
        return None
    window_unit = str(raw.get("window_unit", "hours")).lower()
    unit_secs = _UNIT_SECONDS.get(window_unit, 3600)
    window_size = _float(raw.get("window_size", 1), 1)
    window_seconds = window_size * unit_secs
    return QuotaRule(max_runs=max_runs, window_seconds=window_seconds)


def build_quota_from_config(jobs: list) -> JobQuota:
    """Build a JobQuota registry from a list of JobConfig objects."""
    quota = JobQuota()
    for job in jobs:
        raw = getattr(job, "quota", None)
        rule = parse_quota_rule(raw)
        if rule is not None:
            quota.register(job.name, rule)
    return quota
