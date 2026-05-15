"""Capture, store, and retrieve job stdout/stderr output."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class OutputRecord:
    job_name: str
    run_id: str
    stdout: str
    stderr: str
    captured_at: datetime
    exit_code: Optional[int] = None

    def has_output(self) -> bool:
        return bool(self.stdout.strip() or self.stderr.strip())

    def combined(self) -> str:
        parts = []
        if self.stdout.strip():
            parts.append(f"[stdout]\n{self.stdout.rstrip()}")
        if self.stderr.strip():
            parts.append(f"[stderr]\n{self.stderr.rstrip()}")
        return "\n".join(parts) if parts else ""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_output_db(db_path: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_output (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name  TEXT NOT NULL,
                run_id    TEXT NOT NULL,
                stdout    TEXT NOT NULL DEFAULT '',
                stderr    TEXT NOT NULL DEFAULT '',
                exit_code INTEGER,
                captured_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_job_output_run ON job_output(job_name, run_id)"
        )


def save_output(db_path: str, record: OutputRecord) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO job_output (job_name, run_id, stdout, stderr, exit_code, captured_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.job_name,
                record.run_id,
                record.stdout,
                record.stderr,
                record.exit_code,
                record.captured_at.isoformat(),
            ),
        )


def load_output(db_path: str, job_name: str, run_id: str) -> Optional[OutputRecord]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM job_output WHERE job_name=? AND run_id=? ORDER BY id DESC LIMIT 1",
            (job_name, run_id),
        ).fetchone()
    if row is None:
        return None
    return OutputRecord(
        job_name=row["job_name"],
        run_id=row["run_id"],
        stdout=row["stdout"],
        stderr=row["stderr"],
        exit_code=row["exit_code"],
        captured_at=datetime.fromisoformat(row["captured_at"]),
    )


def load_recent_outputs(db_path: str, job_name: str, limit: int = 10) -> list[OutputRecord]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM job_output WHERE job_name=? ORDER BY id DESC LIMIT ?",
            (job_name, limit),
        ).fetchall()
    return [
        OutputRecord(
            job_name=r["job_name"],
            run_id=r["run_id"],
            stdout=r["stdout"],
            stderr=r["stderr"],
            exit_code=r["exit_code"],
            captured_at=datetime.fromisoformat(r["captured_at"]),
        )
        for r in rows
    ]
