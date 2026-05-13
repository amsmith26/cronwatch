"""CLI subcommand: cronwatch schedule — display schedule info for configured jobs."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from cronwatch.config import CronwatchConfig
from cronwatch.job_schedule import schedules_for_config, describe_schedule


def add_schedule_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "schedule",
        help="Show schedule status for all configured jobs",
    )
    p.add_argument(
        "--job",
        metavar="NAME",
        default=None,
        help="Limit output to a single job by name",
    )
    p.add_argument(
        "--overdue-only",
        action="store_true",
        default=False,
        help="Only show jobs that are currently overdue",
    )
    p.set_defaults(func=cmd_schedule)


def cmd_schedule(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    jobs = cfg.jobs
    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            print(f"No job named '{args.job}' found.", file=sys.stderr)
            return 1

    infos = schedules_for_config(jobs)

    if args.overdue_only:
        infos = {name: info for name, info in infos.items() if info.overdue}

    if not infos:
        print("No matching jobs.")
        return 0

    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"Schedule report  (as of {now_str})")
    print("-" * 60)
    for name, info in sorted(infos.items()):
        marker = "[!]" if info.overdue else "   "
        print(f"{marker} {name}: {describe_schedule(info.cron_expr, info.grace_seconds)}")

    overdue_count = sum(1 for i in infos.values() if i.overdue)
    print("-" * 60)
    print(f"Total: {len(infos)}  Overdue: {overdue_count}")
    return 0 if overdue_count == 0 else 2
