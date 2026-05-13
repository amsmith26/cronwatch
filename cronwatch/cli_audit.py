"""CLI sub-commands for inspecting the cronwatch audit log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from cronwatch.audit_log import AuditLog


def add_audit_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="Inspect the cronwatch audit log")
    p.add_argument("--log", default="/var/log/cronwatch/audit.log", help="Path to audit log file")
    sub = p.add_subparsers(dest="audit_cmd")

    tail_p = sub.add_parser("tail", help="Show the last N audit entries")
    tail_p.add_argument("-n", type=int, default=20, help="Number of entries to show")
    tail_p.add_argument("--json", dest="as_json", action="store_true", help="Output raw JSON lines")

    job_p = sub.add_parser("job", help="Show audit entries for a specific job")
    job_p.add_argument("job_name", help="Job name to filter by")
    job_p.add_argument("--json", dest="as_json", action="store_true", help="Output raw JSON lines")


def _format_entry(entry: dict) -> str:  # type: ignore[type-arg]
    ts = entry.get("ts", "?")
    event = entry.get("event", "?")
    job = entry.get("job", "?")
    extras = {k: v for k, v in entry.items() if k not in ("ts", "event", "job")}
    line = f"[{ts}] {event:<20} job={job}"
    if extras:
        extra_str = "  ".join(f"{k}={v}" for k, v in extras.items())
        line += f"  {extra_str}"
    return line


def cmd_audit(args: argparse.Namespace) -> int:
    log = AuditLog(args.log)

    if args.audit_cmd == "tail" or args.audit_cmd is None:
        n = getattr(args, "n", 20)
        entries = log.tail(n)
    elif args.audit_cmd == "job":
        entries = log.read_for_job(args.job_name)
    else:
        print(f"Unknown audit sub-command: {args.audit_cmd}", file=sys.stderr)
        return 1

    if not entries:
        print("No audit entries found.")
        return 0

    as_json = getattr(args, "as_json", False)
    for entry in entries:
        if as_json:
            print(json.dumps(entry))
        else:
            print(_format_entry(entry))

    return 0
