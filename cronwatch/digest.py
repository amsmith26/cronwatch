"""Periodic digest report generation and delivery for cronwatch."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronwatch.alerter import dispatch_alert
from cronwatch.config import AlertConfig, CronwatchConfig
from cronwatch.history import load_records
from cronwatch.reporter import Report, as_text, build_summary
from cronwatch.tracker import RunRecord

log = logging.getLogger(__name__)


@dataclass
class DigestResult:
    jobs_included: int
    sent: bool
    period_hours: int


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def collect_recent_records(
    cfg: CronwatchConfig,
    db_path: str,
    period_hours: int,
) -> List[RunRecord]:
    """Load records from all configured jobs within the given time window."""
    cutoff = _utcnow() - timedelta(hours=period_hours)
    all_records: List[RunRecord] = []
    for job in cfg.jobs:
        records = load_records(db_path, job.name)
        recent = [r for r in records if r.started_at >= cutoff]
        all_records.extend(recent)
    return all_records


def build_digest(
    cfg: CronwatchConfig,
    db_path: str,
    period_hours: int = 24,
) -> Optional[Report]:
    """Build a digest Report covering *period_hours* of history.

    Returns None when there are no records to report.
    """
    records = collect_recent_records(cfg, db_path, period_hours)
    if not records:
        log.debug("digest: no records in the last %d hours", period_hours)
        return None

    job_map = {j.name: j for j in cfg.jobs}
    summaries = []
    for job in cfg.jobs:
        job_records = [r for r in records if r.job_name == job.name]
        if job_records:
            summaries.append(build_summary(job_map[job.name], job_records))

    return Report(generated_at=_utcnow(), summaries=summaries)


def send_digest(
    cfg: CronwatchConfig,
    alert_cfg: AlertConfig,
    db_path: str,
    period_hours: int = 24,
) -> DigestResult:
    """Build and dispatch a digest email. Returns a DigestResult."""
    report = build_digest(cfg, db_path, period_hours)
    if report is None:
        return DigestResult(jobs_included=0, sent=False, period_hours=period_hours)

    subject = f"[cronwatch] Daily digest — {report.generated_at.strftime('%Y-%m-%d')}"
    body = as_text(report)
    sent = dispatch_alert(alert_cfg, subject, body)
    log.info("digest sent=%s jobs=%d", sent, len(report.summaries))
    return DigestResult(jobs_included=len(report.summaries), sent=sent, period_hours=period_hours)
