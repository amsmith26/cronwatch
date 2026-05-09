"""Parse dependency declarations from job config dicts."""

from __future__ import annotations

from typing import Any, Dict, List


def parse_depends_on(raw: Any) -> List[str]:
    """Normalise the ``depends_on`` field to a list of strings.

    Accepts:
    - ``None`` / missing  -> ``[]``
    - a single string     -> ``[string]``
    - a list of strings   -> returned as-is (copies)
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw]
    raise ValueError(f"depends_on must be a string or list, got {type(raw).__name__!r}")


def extract_dependency_map(jobs_raw: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Return a mapping of job_name -> [dependency names] from raw YAML job dicts.

    Jobs without a ``depends_on`` key are omitted.
    """
    result: Dict[str, List[str]] = {}
    for job in jobs_raw:
        name = job.get("name", "")
        deps = parse_depends_on(job.get("depends_on"))
        if deps:
            result[name] = deps
    return result


def detect_cycles(dependency_map: Dict[str, List[str]]) -> List[str]:
    """Return a list of job names that participate in a dependency cycle.

    Uses depth-first search with colouring (white/grey/black).
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour: Dict[str, int] = {}
    cycle_members: List[str] = []

    def dfs(node: str) -> bool:
        colour[node] = GREY
        for neighbour in dependency_map.get(node, []):
            state = colour.get(neighbour, WHITE)
            if state == GREY:
                cycle_members.append(neighbour)
                return True
            if state == WHITE and dfs(neighbour):
                cycle_members.append(node)
                return True
        colour[node] = BLACK
        return False

    for job in list(dependency_map.keys()):
        if colour.get(job, WHITE) == WHITE:
            dfs(job)

    return list(dict.fromkeys(cycle_members))  # deduplicate, preserve order
