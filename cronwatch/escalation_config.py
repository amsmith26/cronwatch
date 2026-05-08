"""Parse escalation policy from a config mapping."""

from __future__ import annotations

from typing import Any, Dict, Optional

from cronwatch.escalation import EscalationPolicy


def parse_escalation_policy(
    raw: Optional[Dict[str, Any]]
) -> EscalationPolicy:
    """Build an EscalationPolicy from a raw YAML/dict mapping.

    Accepted keys (all optional):
        warn_after      – int, default 2
        critical_after  – int, default 5
        reset_after     – int, default 1
    """
    if not raw:
        return EscalationPolicy()

    def _int(key: str, default: int) -> int:
        val = raw.get(key, default)
        try:
            return int(val)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"escalation.{key} must be an integer, got {val!r}"
            ) from exc

    warn_after = _int("warn_after", 2)
    critical_after = _int("critical_after", 5)
    reset_after = _int("reset_after", 1)

    if warn_after < 1:
        raise ValueError("escalation.warn_after must be >= 1")
    if critical_after < warn_after:
        raise ValueError(
            "escalation.critical_after must be >= escalation.warn_after"
        )
    if reset_after < 1:
        raise ValueError("escalation.reset_after must be >= 1")

    return EscalationPolicy(
        warn_after=warn_after,
        critical_after=critical_after,
        reset_after=reset_after,
    )
