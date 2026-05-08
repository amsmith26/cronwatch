"""Tag-based filtering for cron jobs.

Allows selecting subsets of jobs by one or more tags defined in JobConfig.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from cronwatch.config import JobConfig


def jobs_with_tag(jobs: Iterable[JobConfig], tag: str) -> List[JobConfig]:
    """Return jobs whose tag list contains *tag* (case-insensitive)."""
    tag_lower = tag.strip().lower()
    return [
        j for j in jobs
        if tag_lower in (t.strip().lower() for t in (j.tags or []))
    ]


def jobs_matching_tags(
    jobs: Iterable[JobConfig],
    tags: Iterable[str],
    *,
    require_all: bool = False,
) -> List[JobConfig]:
    """Filter jobs by multiple tags.

    Args:
        jobs: Iterable of JobConfig objects to filter.
        tags: Tags to match against.
        require_all: If True every tag must be present (AND); otherwise any
                     tag is sufficient (OR, default).

    Returns:
        Filtered list of JobConfig objects.
    """
    tag_set = {t.strip().lower() for t in tags}
    if not tag_set:
        return list(jobs)

    result = []
    for job in jobs:
        job_tags = {t.strip().lower() for t in (job.tags or [])}
        if require_all:
            if tag_set <= job_tags:
                result.append(job)
        else:
            if tag_set & job_tags:
                result.append(job)
    return result


def collect_all_tags(jobs: Iterable[JobConfig]) -> List[str]:
    """Return a sorted, deduplicated list of all tags used across *jobs*."""
    seen: set[str] = set()
    for job in jobs:
        for tag in job.tags or []:
            seen.add(tag.strip().lower())
    return sorted(seen)
