"""Job dependency tracking — ensures jobs run in declared order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from cronwatch.tracker import RunStatus, JobTracker


@dataclass
class DependencyGraph:
    """Directed graph of job dependencies."""

    # job_name -> list of job names that must have succeeded first
    edges: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, job: str, depends_on: List[str]) -> None:
        """Register that *job* depends on each name in *depends_on*."""
        self.edges[job] = list(depends_on)

    def dependencies_of(self, job: str) -> List[str]:
        return self.edges.get(job, [])

    def all_jobs(self) -> Set[str]:
        jobs: Set[str] = set(self.edges.keys())
        for deps in self.edges.values():
            jobs.update(deps)
        return jobs


def build_graph_from_config(jobs) -> DependencyGraph:
    """Build a DependencyGraph from a list of JobConfig objects."""
    graph = DependencyGraph()
    for job in jobs:
        deps = getattr(job, "depends_on", None) or []
        if deps:
            graph.add(job.name, deps)
    return graph


def dependencies_satisfied(
    job_name: str,
    graph: DependencyGraph,
    tracker: JobTracker,
    since: Optional[float] = None,
) -> bool:
    """Return True when every dependency of *job_name* last finished successfully.

    Args:
        job_name: The job whose dependencies are checked.
        graph: Dependency graph.
        tracker: JobTracker holding run records.
        since: Optional epoch timestamp; the successful run must be *after* this
               value.  Pass the job's own scheduled start time to ensure the
               dependency ran in the current cycle.
    """
    for dep in graph.dependencies_of(job_name):
        records = tracker.records.get(dep, [])
        if not records:
            return False
        last = records[-1]
        if last.status != RunStatus.SUCCESS:
            return False
        if since is not None:
            finished = last.finished_at or 0.0
            if finished < since:
                return False
    return True


def blocked_jobs(
    graph: DependencyGraph,
    tracker: JobTracker,
    since: Optional[float] = None,
) -> List[str]:
    """Return names of jobs whose dependencies are *not* yet satisfied."""
    return [
        job
        for job in graph.edges
        if not dependencies_satisfied(job, graph, tracker, since=since)
    ]
