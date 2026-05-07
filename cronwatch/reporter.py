"""Generate summary reports of cron job run history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cronwatch.tracker import JobTracker, RunRecord, RunStatus


@dataclass
class JobSummary:
    job_name: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    missed_runs: int = 0
    avg_duration_seconds: Optional[float] = None
    last_run_at: Optional[datetime] = None
    last_status: Optional[RunStatus] = None

    @property
    def success_rate(self) -> Optional[float]:
        if self.total_runs == 0:
            return None
        return self.successful_runs / self.total_runs * 100.0


@dataclass
class Report:
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summaries: Dict[str, JobSummary] = field(default_factory=dict)

    def as_text(self) -> str:
        lines = [
            f"CronWatch Report — {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "=" * 60,
        ]
        if not self.summaries:
            lines.append("No job data available.")
            return "\n".join(lines)
        for name, s in self.summaries.items():
            rate = f"{s.success_rate:.1f}%" if s.success_rate is not None else "N/A"
            avg = f"{s.avg_duration_seconds:.1f}s" if s.avg_duration_seconds is not None else "N/A"
            last = s.last_run_at.strftime("%Y-%m-%d %H:%M:%S UTC") if s.last_run_at else "never"
            lines += [
                f"Job: {name}",
                f"  Runs      : {s.total_runs} (ok={s.successful_runs} fail={s.failed_runs} missed={s.missed_runs})",
                f"  Success % : {rate}",
                f"  Avg dur   : {avg}",
                f"  Last run  : {last}  status={s.last_status.value if s.last_status else 'N/A'}",
                "-" * 60,
            ]
        return "\n".join(lines)


def build_summary(job_name: str, records: List[RunRecord]) -> JobSummary:
    s = JobSummary(job_name=job_name)
    durations: List[float] = []
    for r in records:
        s.total_runs += 1
        if r.status == RunStatus.SUCCESS:
            s.successful_runs += 1
        elif r.status == RunStatus.FAILURE:
            s.failed_runs += 1
        elif r.status == RunStatus.MISSED:
            s.missed_runs += 1
        if r.duration_seconds is not None:
            durations.append(r.duration_seconds)
        if s.last_run_at is None or (r.started_at and r.started_at > s.last_run_at):
            s.last_run_at = r.started_at
            s.last_status = r.status
    if durations:
        s.avg_duration_seconds = sum(durations) / len(durations)
    return s


def generate_report(tracker: JobTracker) -> Report:
    report = Report()
    for job_name, records in tracker.history.items():
        report.summaries[job_name] = build_summary(job_name, records)
    return report
