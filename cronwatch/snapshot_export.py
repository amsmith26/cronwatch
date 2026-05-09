"""Render a SystemSnapshot as JSON or plain text."""

from __future__ import annotations

import json
from typing import Any, Dict

from cronwatch.snapshot import JobSnapshot, SystemSnapshot


def _job_to_dict(j: JobSnapshot) -> Dict[str, Any]:
    return {
        "name": j.name,
        "schedule": j.schedule,
        "tags": j.tags,
        "total_runs": j.total_runs,
        "success_rate": round(j.success_rate, 4),
        "avg_duration_seconds": round(j.avg_duration_seconds, 3),
        "last_status": j.last_status,
        "last_finished_at": j.last_finished_at.isoformat() if j.last_finished_at else None,
        "is_overdue": j.is_overdue,
        "seconds_until_next_run": round(j.seconds_until_next_run, 1),
    }


def render_json(snapshot: SystemSnapshot, indent: int = 2) -> str:
    """Return the snapshot serialised as a JSON string."""
    payload: Dict[str, Any] = {
        "captured_at": snapshot.captured_at.isoformat(),
        "total_jobs": snapshot.total_jobs,
        "overdue_count": snapshot.overdue_count,
        "failing_count": snapshot.failing_count,
        "jobs": [_job_to_dict(j) for j in snapshot.jobs],
    }
    return json.dumps(payload, indent=indent)


def render_text(snapshot: SystemSnapshot) -> str:
    """Return a human-readable summary table."""
    lines = [
        f"Snapshot at {snapshot.captured_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Jobs: {snapshot.total_jobs}  Overdue: {snapshot.overdue_count}  Failing: {snapshot.failing_count}",
        "-" * 72,
        f"{'NAME':<24} {'SCHEDULE':<18} {'RUNS':>6} {'SUCCESS%':>9} {'OVERDUE':>8}",
        "-" * 72,
    ]
    for j in snapshot.jobs:
        overdue_flag = "YES" if j.is_overdue else "no"
        pct = f"{j.success_rate * 100:.1f}%"
        lines.append(
            f"{j.name:<24} {j.schedule:<18} {j.total_runs:>6} {pct:>9} {overdue_flag:>8}"
        )
    lines.append("-" * 72)
    return "\n".join(lines)
