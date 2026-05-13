"""Job annotation support: attach arbitrary key-value metadata to job runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Annotation:
    """A single key/value annotation attached to a job run."""

    key: str
    value: str

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


@dataclass
class AnnotationSet:
    """Collection of annotations for a single job run."""

    job_name: str
    run_id: str
    annotations: Dict[str, str] = field(default_factory=dict)

    def add(self, key: str, value: str) -> None:
        """Add or overwrite an annotation."""
        if not key:
            raise ValueError("Annotation key must not be empty")
        self.annotations[key] = value

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return the value for *key*, or *default* if absent."""
        return self.annotations.get(key, default)

    def remove(self, key: str) -> bool:
        """Remove *key*; return True if it existed."""
        if key in self.annotations:
            del self.annotations[key]
            return True
        return False

    def as_list(self) -> List[Annotation]:
        """Return annotations as a sorted list of :class:`Annotation` objects."""
        return [Annotation(k, v) for k, v in sorted(self.annotations.items())]

    def __len__(self) -> int:
        return len(self.annotations)


class AnnotationStore:
    """In-memory store mapping (job_name, run_id) -> AnnotationSet."""

    def __init__(self) -> None:
        self._store: Dict[tuple, AnnotationSet] = {}

    def _key(self, job_name: str, run_id: str) -> tuple:
        return (job_name, run_id)

    def annotate(self, job_name: str, run_id: str, key: str, value: str) -> None:
        """Add or update a single annotation for the given run."""
        k = self._key(job_name, run_id)
        if k not in self._store:
            self._store[k] = AnnotationSet(job_name=job_name, run_id=run_id)
        self._store[k].add(key, value)

    def get_annotations(self, job_name: str, run_id: str) -> Optional[AnnotationSet]:
        """Return the :class:`AnnotationSet` for a run, or None."""
        return self._store.get(self._key(job_name, run_id))

    def remove_annotation(self, job_name: str, run_id: str, key: str) -> bool:
        """Remove a single annotation; return True if it was present."""
        ann_set = self.get_annotations(job_name, run_id)
        if ann_set is None:
            return False
        return ann_set.remove(key)

    def all_for_job(self, job_name: str) -> List[AnnotationSet]:
        """Return all annotation sets for a given job, sorted by run_id."""
        return sorted(
            [v for (j, _), v in self._store.items() if j == job_name],
            key=lambda s: s.run_id,
        )

    def clear(self, job_name: str, run_id: str) -> None:
        """Delete the entire annotation set for a run."""
        self._store.pop(self._key(job_name, run_id), None)
