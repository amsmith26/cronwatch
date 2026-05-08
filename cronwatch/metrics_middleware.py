"""Integration helpers: update the metrics registry from tracker RunRecords."""
from __future__ import annotations

from typing import Optional

from cronwatch.metrics import MetricsRegistry, registry as _default_registry
from cronwatch.tracker import RunRecord, RunStatus


def ingest_record(
    record: RunRecord,
    reg: Optional[MetricsRegistry] = None,
) -> None:
    """Push a finished RunRecord into the metrics registry.

    Only SUCCESS and FAILURE records carry duration; MISSED records do not.
    """
    reg = reg or _default_registry
    name = record.job_name

    if record.status == RunStatus.SUCCESS:
        reg.record_success(name, record.duration or 0.0)
    elif record.status == RunStatus.FAILURE:
        reg.record_failure(name, record.duration or 0.0)
    elif record.status == RunStatus.MISSED:
        reg.record_missed(name)


def ingest_records(
    records: list[RunRecord],
    reg: Optional[MetricsRegistry] = None,
) -> None:
    """Bulk-ingest a list of RunRecords (e.g. loaded from history)."""
    reg = reg or _default_registry
    for r in records:
        ingest_record(r, reg=reg)
