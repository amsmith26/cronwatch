"""Attach and query arbitrary key-value labels on job configs."""

from __future__ import annotations

from typing import Dict, Iterable, List

from cronwatch.config import JobConfig


def get_labels(job: JobConfig) -> Dict[str, str]:
    """Return the labels dict for *job*, defaulting to empty."""
    return getattr(job, "labels", None) or {}


def has_label(job: JobConfig, key: str, value: str | None = None) -> bool:
    """Return True if *job* has *key* (optionally matching *value*)."""
    labels = get_labels(job)
    if key not in labels:
        return False
    if value is None:
        return True
    return labels[key] == value


def jobs_with_label(
    jobs: Iterable[JobConfig],
    key: str,
    value: str | None = None,
) -> List[JobConfig]:
    """Filter *jobs* to those carrying the given label key/value."""
    return [j for j in jobs if has_label(j, key, value)]


def collect_label_keys(jobs: Iterable[JobConfig]) -> List[str]:
    """Return a sorted list of all distinct label keys across *jobs*."""
    keys: set[str] = set()
    for job in jobs:
        keys.update(get_labels(job).keys())
    return sorted(keys)


def label_index(
    jobs: Iterable[JobConfig],
) -> Dict[str, Dict[str, List[JobConfig]]]:
    """Build a nested index: {key: {value: [jobs]}}."""
    index: Dict[str, Dict[str, List[JobConfig]]] = {}
    for job in jobs:
        for k, v in get_labels(job).items():
            index.setdefault(k, {}).setdefault(v, []).append(job)
    return index
