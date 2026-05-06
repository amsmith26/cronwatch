"""Job execution tracker — records run history and detects missed/failed runs."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from cronwatch.config import JobConfig


class RunStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    MISSED = "missed"


@dataclass
class RunRecord:
    job_name: str
    status: RunStatus
    started_at: float
    finished_at: Optional[float] = None
    exit_code: Optional[int] = None
    message: str = ""

    @property
    def duration(self) -> Optional[float]:
        if self.finished_at is not None:
            return self.finished_at - self.started_at
        return None


@dataclass
class JobTracker:
    config: JobConfig
    history: List[RunRecord] = field(default_factory=list)
    _last_expected_at: Optional[float] = field(default=None, repr=False)

    def record_start(self, started_at: Optional[float] = None) -> RunRecord:
        record = RunRecord(
            job_name=self.config.name,
            status=RunStatus.SUCCESS,
            started_at=started_at if started_at is not None else time.time(),
        )
        self.history.append(record)
        return record

    def record_finish(self, record: RunRecord, exit_code: int, finished_at: Optional[float] = None) -> None:
        record.finished_at = finished_at if finished_at is not None else time.time()
        record.exit_code = exit_code
        if exit_code != 0:
            record.status = RunStatus.FAILURE
            record.message = f"Exited with code {exit_code}"

    def record_missed(self, expected_at: float) -> RunRecord:
        record = RunRecord(
            job_name=self.config.name,
            status=RunStatus.MISSED,
            started_at=expected_at,
            finished_at=expected_at,
            message="Job did not run within the expected window",
        )
        self.history.append(record)
        return record

    def last_run(self) -> Optional[RunRecord]:
        completed = [r for r in self.history if r.finished_at is not None]
        return completed[-1] if completed else None

    def failed_runs(self) -> List[RunRecord]:
        return [r for r in self.history if r.status in (RunStatus.FAILURE, RunStatus.MISSED)]


class TrackerRegistry:
    def __init__(self) -> None:
        self._trackers: Dict[str, JobTracker] = {}

    def register(self, config: JobConfig) -> JobTracker:
        tracker = JobTracker(config=config)
        self._trackers[config.name] = tracker
        return tracker

    def get(self, name: str) -> Optional[JobTracker]:
        return self._trackers.get(name)

    def all(self) -> List[JobTracker]:
        return list(self._trackers.values())
