"""Retention policy: prune old run records from the history database."""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from cronwatch.history import _connect

log = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def prune_records(
    db_path: str,
    job_name: Optional[str] = None,
    older_than_days: int = 30,
) -> int:
    """Delete records older than *older_than_days*.

    If *job_name* is given, only that job's records are pruned.
    Returns the number of rows deleted.
    """
    if older_than_days < 1:
        raise ValueError("older_than_days must be >= 1")

    cutoff: datetime = _utcnow() - timedelta(days=older_than_days)
    cutoff_ts: float = cutoff.timestamp()

    conn: sqlite3.Connection = _connect(db_path)
    try:
        if job_name:
            cur = conn.execute(
                "DELETE FROM runs WHERE job_name = ? AND started_at < ?",
                (job_name, cutoff_ts),
            )
        else:
            cur = conn.execute(
                "DELETE FROM runs WHERE started_at < ?",
                (cutoff_ts,),
            )
        conn.commit()
        deleted: int = cur.rowcount
    finally:
        conn.close()

    log.info(
        "Pruned %d record(s) older than %d day(s)%s",
        deleted,
        older_than_days,
        f" for job '{job_name}'" if job_name else "",
    )
    return deleted


def prune_excess_records(
    db_path: str,
    job_name: str,
    keep: int = 100,
) -> int:
    """Keep only the *keep* most-recent records for *job_name*.

    Returns the number of rows deleted.
    """
    if keep < 1:
        raise ValueError("keep must be >= 1")

    conn: sqlite3.Connection = _connect(db_path)
    try:
        cur = conn.execute(
            """
            DELETE FROM runs
            WHERE job_name = ?
              AND rowid NOT IN (
                SELECT rowid FROM runs
                WHERE job_name = ?
                ORDER BY started_at DESC
                LIMIT ?
              )
            """,
            (job_name, job_name, keep),
        )
        conn.commit()
        deleted = cur.rowcount
    finally:
        conn.close()

    log.info("Pruned %d excess record(s) for job '%s' (keep=%d)", deleted, job_name, keep)
    return deleted
