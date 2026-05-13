"""Parse retry policy from a job config dict."""
from __future__ import annotations

from typing import Any, Dict, Optional

from cronwatch.job_retry import RetryPolicy

_DEFAULTS = {
    "max_attempts": 3,
    "delay_seconds": 60.0,
    "backoff_factor": 1.0,
    "max_delay_seconds": 3600.0,
}


def _float(val: Any, default: float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _int(val: Any, default: int) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def parse_retry_policy(raw: Optional[Dict[str, Any]]) -> RetryPolicy:
    """Build a :class:`RetryPolicy` from a raw YAML mapping.

    Missing keys fall back to defaults.  Passing ``None`` or an empty
    dict returns the default policy.
    """
    if not raw:
        return RetryPolicy(**_DEFAULTS)  # type: ignore[arg-type]

    return RetryPolicy(
        max_attempts=_int(raw.get("max_attempts"), _DEFAULTS["max_attempts"]),
        delay_seconds=_float(raw.get("delay_seconds"), _DEFAULTS["delay_seconds"]),
        backoff_factor=_float(raw.get("backoff_factor"), _DEFAULTS["backoff_factor"]),
        max_delay_seconds=_float(
            raw.get("max_delay_seconds"), _DEFAULTS["max_delay_seconds"]
        ),
    )
