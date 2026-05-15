"""Parse cost configuration from YAML job definitions."""
from __future__ import annotations

from typing import Any, Dict, List

from cronwatch.job_cost import CostRegistry, CostRule


def _float(val: Any, default: float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def parse_cost_rule(job_name: str, raw: Any) -> CostRule:
    """Build a CostRule from a job's 'cost' config block (or None)."""
    if not raw or not isinstance(raw, dict):
        return CostRule(job_name=job_name)
    return CostRule(
        job_name=job_name,
        cost_per_second=_float(raw.get("per_second"), 0.0),
        fixed_cost=_float(raw.get("fixed"), 0.0),
        currency=str(raw.get("currency", "USD")),
    )


def build_cost_registry(jobs: List[Any]) -> CostRegistry:
    """Build a CostRegistry from a list of JobConfig objects.

    Each job may expose a ``cost`` attribute (dict) parsed from YAML.
    Jobs without a cost block are silently skipped.
    """
    registry = CostRegistry()
    for job in jobs:
        raw_cost = getattr(job, "cost", None)
        if raw_cost is None:
            continue
        rule = parse_cost_rule(job.name, raw_cost)
        registry.register(rule)
    return registry


def cost_summary_lines(registry: CostRegistry) -> List[str]:
    """Return human-readable cost summary lines."""
    summary = registry.summary()
    if not summary:
        return ["No cost data available."]
    lines = []
    for job_name, total in sorted(summary.items()):
        entries = registry.all_entries(job_name)
        currency = entries[0].currency if entries else "USD"
        lines.append(f"{job_name}: {total:.4f} {currency} over {len(entries)} run(s)")
    return lines
