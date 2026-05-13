"""Concurrency control: limit how many instances of a job may run at once."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional


@dataclass
class ConcurrencyRule:
    max_concurrent: int = 1


@dataclass
class _Slot:
    running: int = 0


class JobConcurrencyGuard:
    """Thread-safe guard that enforces per-job concurrency limits."""

    def __init__(self) -> None:
        self._lock: Lock = Lock()
        self._rules: Dict[str, ConcurrencyRule] = {}
        self._slots: Dict[str, _Slot] = {}

    def register(self, job_name: str, rule: ConcurrencyRule) -> None:
        """Register a concurrency rule for *job_name*."""
        with self._lock:
            self._rules[job_name] = rule
            self._slots.setdefault(job_name, _Slot())

    def _get_slot(self, job_name: str) -> _Slot:
        slot = self._slots.get(job_name)
        if slot is None:
            slot = _Slot()
            self._slots[job_name] = slot
        return slot

    def acquire(self, job_name: str) -> bool:
        """Try to acquire a slot for *job_name*.

        Returns True when a slot was granted, False when the limit is already
        reached or the job has no registered rule.
        """
        with self._lock:
            rule = self._rules.get(job_name)
            if rule is None:
                return True  # unregistered jobs are unconstrained
            slot = self._get_slot(job_name)
            if slot.running >= rule.max_concurrent:
                return False
            slot.running += 1
            return True

    def release(self, job_name: str) -> None:
        """Release a previously acquired slot for *job_name*."""
        with self._lock:
            slot = self._slots.get(job_name)
            if slot and slot.running > 0:
                slot.running -= 1

    def running_count(self, job_name: str) -> int:
        """Return the current number of running instances for *job_name*."""
        with self._lock:
            return self._slots.get(job_name, _Slot()).running

    def is_at_limit(self, job_name: str) -> bool:
        """Return True when *job_name* has reached its concurrency limit."""
        with self._lock:
            rule = self._rules.get(job_name)
            if rule is None:
                return False
            slot = self._slots.get(job_name, _Slot())
            return slot.running >= rule.max_concurrent


def parse_concurrency_rule(cfg: Optional[dict]) -> ConcurrencyRule:
    """Build a ConcurrencyRule from a raw config dict (or None)."""
    if not cfg:
        return ConcurrencyRule()
    raw = cfg.get("max_concurrent", 1)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 1
    return ConcurrencyRule(max_concurrent=max(1, value))
