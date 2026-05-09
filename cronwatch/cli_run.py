"""CLI sub-command: ``cronwatch run <job>`` — execute a job on demand."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from cronwatch.config import CronwatchConfig
from cronwatch.job_runner import run_job
from cronwatch.tracker import JobTracker


def add_run_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *run* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "run",
        help="Execute a configured job immediately and report the result.",
    )
    p.add_argument(
        "job_name",
        metavar="JOB",
        help="Name of the job as defined in the config file.",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=None,
        metavar="SECONDS",
        help="Override the per-job grace_period timeout (seconds).",
    )
    p.set_defaults(func=cmd_run)


def cmd_run(
    args: argparse.Namespace,
    cfg: CronwatchConfig,
    tracker: Optional[JobTracker] = None,
) -> int:
    """Entry point for the *run* sub-command.

    Returns 0 on success, 1 on job failure, 2 on configuration error.
    """
    job = next((j for j in cfg.jobs if j.name == args.job_name), None)
    if job is None:
        print(
            f"cronwatch run: job '{args.job_name}' not found in config.",
            file=sys.stderr,
        )
        return 2

    if tracker is None:
        tracker = JobTracker()
        tracker.register(job)

    print(f"Running job: {job.name}")
    success = run_job(job, tracker, timeout=args.timeout)

    records = tracker.get_records(job.name)
    last = records[-1] if records else None

    if last:
        dur = f"{last.duration:.1f}s" if last.duration is not None else "n/a"
        print(f"Status : {'SUCCESS' if success else 'FAILURE'}")
        print(f"Exit   : {last.exit_code}")
        print(f"Duration: {dur}")
        if last.output:
            print(f"Output :\n{last.output}")

    return 0 if success else 1
