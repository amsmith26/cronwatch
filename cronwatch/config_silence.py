"""Load silence rules from a CronwatchConfig-compatible YAML section.

Expected YAML shape (under the top-level key ``silence``):

    silence:
      - job: backup-*
        start: "2024-12-25T00:00:00"
        end:   "2024-12-25T06:00:00"
        reason: Christmas maintenance

This module is intentionally thin so that ``Silencer`` stays independent
of the config layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from cronwatch.silencer import Silencer, SilenceRule, parse_silence_rules


def build_silencer_from_config(raw_config: Dict[str, Any]) -> Silencer:
    """Construct a :class:`Silencer` from the parsed YAML mapping.

    Parameters
    ----------
    raw_config:
        The full parsed YAML dict (same object passed to
        ``CronwatchConfig``).  The ``silence`` key is optional; if absent
        an empty ``Silencer`` is returned.
    """
    raw_rules: List[Dict] = raw_config.get("silence") or []
    rules: List[SilenceRule] = parse_silence_rules(raw_rules)
    silencer = Silencer(rules=rules)
    return silencer


def silencer_summary(silencer: Silencer) -> str:
    """Return a human-readable summary of all registered silence rules."""
    if not silencer.rules:
        return "No silence rules configured."
    lines = [f"Silence rules ({len(silencer.rules)} total):"]
    for r in silencer.rules:
        active_tag = "[ACTIVE]" if r.is_active() else "[inactive]"
        lines.append(
            f"  {active_tag} {r.job_pattern!r}  "
            f"{r.start.isoformat()} → {r.end.isoformat()}"
            + (f"  # {r.reason}" if r.reason else "")
        )
    return "\n".join(lines)
