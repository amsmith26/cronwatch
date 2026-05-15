"""Job checkpoint tracking — persist and query the last successful run time per job."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_checkpoint_db(db_path: str) -> None:
    """Create the checkpoints table if it does not exist."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                job_name  TEXT PRIMARY KEY,
                last_ok   TEXT NOT NULL,
                updated   TEXT NOT NULL
            )
            """
        )


def save_checkpoint(db_path: str, job_name: str, last_ok: datetime) -> None:
    """Upsert the last-successful-run timestamp for *job_name*."""
    now = _utcnow().isoformat()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO checkpoints (job_name, last_ok, updated)
            VALUES (?, ?, ?)
            ON CONFLICT(job_name) DO UPDATE SET last_ok=excluded.last_ok,
                                                updated=excluded.updated
            """,
            (job_name, last_ok.isoformat(), now),
        )


def load_checkpoint(db_path: str, job_name: str) -> Optional[datetime]:
    """Return the last successful run time for *job_name*, or ``None``."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT last_ok FROM checkpoints WHERE job_name = ?",
            (job_name,),
        ).fetchone()
    if row is None:
        return None
    return datetime.fromisoformat(row["last_ok"])


def delete_checkpoint(db_path: str, job_name: str) -> bool:
    """Remove the checkpoint for *job_name*. Returns True if a row was deleted."""
    with _connect(db_path) as conn:
        cur = conn.execute(
            "DELETE FROM checkpoints WHERE job_name = ?", (job_name,)
        )
    return cur.rowcount > 0


def list_checkpoints(db_path: str) -> dict[str, datetime]:
    """Return all checkpoints as a mapping of job_name -> last_ok datetime."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT job_name, last_ok FROM checkpoints ORDER BY job_name"
        ).fetchall()
    return {r["job_name"]: datetime.fromisoformat(r["last_ok"]) for r in rows}
