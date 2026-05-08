"""CLI helpers for the 'prune' sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwatch.config import CronwatchConfig
from cronwatch.retention import prune_excess_records, prune_records


def add_prune_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "prune",
        help="Remove old run records from the history database.",
    )
    p.add_argument(
        "--days",
        type=int,
        default=30,
        metavar="N",
        help="Delete records older than N days (default: 30).",
    )
    p.add_argument(
        "--keep",
        type=int,
        default=None,
        metavar="K",
        help="Also cap each job to at most K most-recent records.",
    )
    p.add_argument(
        "--job",
        default=None,
        metavar="JOB",
        help="Limit pruning to a single job name.",
    )


def cmd_prune(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    """Execute the 'prune' command.  Returns an exit code."""
    db_path: str = cfg.db_path

    if not db_path:
        print("ERROR: db_path not configured.", file=sys.stderr)
        return 1

    total_deleted = 0

    try:
        deleted = prune_records(
            db_path,
            job_name=args.job or None,
            older_than_days=args.days,
        )
        total_deleted += deleted
        print(f"Pruned {deleted} record(s) older than {args.days} day(s).")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.keep is not None:
        jobs = [args.job] if args.job else [j.name for j in cfg.jobs]
        for job_name in jobs:
            try:
                d = prune_excess_records(db_path, job_name=job_name, keep=args.keep)
                total_deleted += d
                if d:
                    print(f"  Pruned {d} excess record(s) for job '{job_name}' (keep={args.keep}).")
            except ValueError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1

    print(f"Total records removed: {total_deleted}")
    return 0
