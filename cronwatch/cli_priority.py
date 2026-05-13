"""CLI sub-command: `cronwatch priority` — list jobs ordered by priority."""
from __future__ import annotations

import argparse
import sys
from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.job_priority import Priority, get_priority, jobs_at_or_above, sort_by_priority


def add_priority_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "priority",
        help="List jobs ordered by priority",
    )
    p.add_argument(
        "--min",
        dest="min_priority",
        choices=["low", "normal", "high", "critical"],
        default="low",
        help="Only show jobs at or above this priority (default: low)",
    )
    p.add_argument(
        "--asc",
        action="store_true",
        default=False,
        help="Sort ascending (lowest priority first)",
    )
    p.set_defaults(func=cmd_priority)


def cmd_priority(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    from cronwatch.job_priority import _NAME_MAP  # local import to avoid circularity

    threshold = _NAME_MAP.get(args.min_priority, Priority.LOW)
    jobs = jobs_at_or_above(cfg.jobs, threshold)
    jobs = sort_by_priority(jobs, descending=not args.asc)

    if not jobs:
        print("No jobs match the given priority filter.")
        return 0

    col_w = max(len(j.name) for j in jobs)
    header = f"{'JOB':<{col_w}}  PRIORITY"
    print(header)
    print("-" * len(header))
    for job in jobs:
        prio = get_priority(job)
        print(f"{job.name:<{col_w}}  {prio.name}")

    return 0
