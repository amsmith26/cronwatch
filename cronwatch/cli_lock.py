"""CLI sub-commands for inspecting and clearing cronwatch job locks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.job_lock import JobLock

_DEFAULT_LOCK_DIR = "/tmp/cronwatch"


def add_lock_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register *lock* sub-commands onto *subparsers*."""
    p = subparsers.add_parser("lock", help="Manage job run-locks")
    sp = p.add_subparsers(dest="lock_cmd", required=True)

    # lock list
    ls = sp.add_parser("list", help="List active locks")
    ls.add_argument(
        "--lock-dir", default=_DEFAULT_LOCK_DIR, help="Directory that holds lock files"
    )

    # lock clear
    cl = sp.add_parser("clear", help="Force-remove a stale or live lock")
    cl.add_argument("job", help="Job name whose lock should be removed")
    cl.add_argument(
        "--lock-dir", default=_DEFAULT_LOCK_DIR, help="Directory that holds lock files"
    )

    p.set_defaults(func=cmd_lock)


def cmd_lock(args: argparse.Namespace) -> int:
    if args.lock_cmd == "list":
        return _cmd_list(args)
    if args.lock_cmd == "clear":
        return _cmd_clear(args)
    return 1


def _cmd_list(args: argparse.Namespace) -> int:
    lock_dir = Path(args.lock_dir)
    if not lock_dir.exists():
        print("No lock directory found — no jobs are locked.")
        return 0

    lock_files = sorted(lock_dir.glob("*.lock"))
    if not lock_files:
        print("No active locks.")
        return 0

    rows = []
    for lf in lock_files:
        job_name = lf.stem
        jl = JobLock(job_name, lock_dir=str(lock_dir))
        try:
            pid = int(lf.read_text().strip())
        except ValueError:
            pid = -1
        status = "ACTIVE" if jl.is_locked() else "STALE"
        rows.append((job_name, pid, status))

    print(f"{'JOB':<30} {'PID':>8}  STATUS")
    print("-" * 50)
    for name, pid, status in rows:
        print(f"{name:<30} {pid:>8}  {status}")
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    jl = JobLock(args.job, lock_dir=args.lock_dir)
    if not Path(args.lock_dir, f"{args.job}.lock").exists():
        print(f"No lock file found for job '{args.job}'.")
        return 1
    jl.release()
    print(f"Lock for '{args.job}' removed.")
    return 0
