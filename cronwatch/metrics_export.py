"""Export collected metrics as Prometheus-compatible plain text."""
from __future__ import annotations

from typing import Optional

from cronwatch.metrics import MetricsRegistry, registry as _default_registry

_HEADER = "# cronwatch metrics\n"


def _gauge(name: str, labels: str, value: float) -> str:
    return f"cronwatch_{name}{{{labels}}} {value}\n"


def render_prometheus(
    reg: Optional[MetricsRegistry] = None,
) -> str:
    """Return a Prometheus text-format string for all tracked jobs."""
    reg = reg or _default_registry
    lines: list[str] = [_HEADER]

    for m in reg.all_metrics():
        lbl = f'job="{m.job_name}"'
        lines.append(_gauge("total_runs", lbl, m.total_runs))
        lines.append(_gauge("successful_runs", lbl, m.successful_runs))
        lines.append(_gauge("failed_runs", lbl, m.failed_runs))
        lines.append(_gauge("missed_runs", lbl, m.missed_runs))
        lines.append(_gauge("success_rate", lbl, round(m.success_rate, 4)))
        lines.append(_gauge("avg_duration_seconds", lbl, round(m.avg_duration, 4)))
        if m.last_run_ts is not None:
            lines.append(_gauge("last_run_timestamp", lbl, m.last_run_ts))
        if m.last_success_ts is not None:
            lines.append(_gauge("last_success_timestamp", lbl, m.last_success_ts))
        if m.last_failure_ts is not None:
            lines.append(_gauge("last_failure_timestamp", lbl, m.last_failure_ts))

    return "".join(lines)


def render_text(reg: Optional[MetricsRegistry] = None) -> str:
    """Return a human-readable summary table."""
    reg = reg or _default_registry
    metrics = reg.all_metrics()
    if not metrics:
        return "No metrics collected yet.\n"

    header = f"{'Job':<30} {'Runs':>6} {'OK':>6} {'FAIL':>6} {'MISS':>6} {'OK%':>7} {'AvgDur':>9}\n"
    sep = "-" * len(header.rstrip()) + "\n"
    rows = [header, sep]
    for m in sorted(metrics, key=lambda x: x.job_name):
        rows.append(
            f"{m.job_name:<30} {m.total_runs:>6} {m.successful_runs:>6} "
            f"{m.failed_runs:>6} {m.missed_runs:>6} "
            f"{m.success_rate * 100:>6.1f}% {m.avg_duration:>8.2f}s\n"
        )
    return "".join(rows)
