"""Persistence layer for run records using a simple SQLite database."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional

from cronwatch.tracker import RunRecord, RunStatus

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS run_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name    TEXT    NOT NULL,
    started_at  REAL    NOT NULL,
    finished_at REAL,
    exit_code   INTEGER,
    status      TEXT    NOT NULL
);
"""


@contextmanager
def _connect(db_path: str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Create the database schema if it does not exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.execute(_CREATE_TABLE)


def save_record(db_path: str, record: RunRecord) -> None:
    """Insert or replace a run record identified by job_name + started_at."""
    sql = """
        INSERT INTO run_records (job_name, started_at, finished_at, exit_code, status)
        VALUES (:job_name, :started_at, :finished_at, :exit_code, :status)
        ON CONFLICT DO NOTHING;
    """
    with _connect(db_path) as conn:
        conn.execute(sql, {
            "job_name": record.job_name,
            "started_at": record.started_at.timestamp(),
            "finished_at": record.finished_at.timestamp() if record.finished_at else None,
            "exit_code": record.exit_code,
            "status": record.status.value,
        })


def load_records(db_path: str, job_name: str, limit: int = 100) -> List[RunRecord]:
    """Return the most recent *limit* records for a given job, newest first."""
    sql = """
        SELECT job_name, started_at, finished_at, exit_code, status
        FROM run_records
        WHERE job_name = ?
        ORDER BY started_at DESC
        LIMIT ?;
    """
    records: List[RunRecord] = []
    with _connect(db_path) as conn:
        for row in conn.execute(sql, (job_name, limit)):
            finished: Optional[datetime] = (
                datetime.utcfromtimestamp(row["finished_at"])
                if row["finished_at"] is not None
                else None
            )
            records.append(RunRecord(
                job_name=row["job_name"],
                started_at=datetime.utcfromtimestamp(row["started_at"]),
                finished_at=finished,
                exit_code=row["exit_code"],
                status=RunStatus(row["status"]),
            ))
    return records
