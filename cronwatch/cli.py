"""Command-line interface for cronwatch."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from cronwatch.config import load_config
from cronwatch.digest import send_digest
from cronwatch.reporter import as_text, build_summary
from cronwatch.history import init_db, load_records
from cronwatch.watcher import run_watch_loop

log = logging.getLogger(__name__)

DEFAULT_DB = "cronwatch.db"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor cron job execution and alert on failures.",
    )
    p.add_argument("--config", "-c", default="cronwatch.yaml", metavar="FILE")
    p.add_argument("--db", default=DEFAULT_DB, metavar="FILE")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    sub = p.add_subparsers(dest="command")

    # watch
    w = sub.add_parser("watch", help="Start the watcher daemon.")
    w.add_argument("--interval", type=int, default=60, help="Poll interval in seconds.")

    # report
    r = sub.add_parser("report", help="Print a summary report.")
    r.add_argument("--job", default=None, help="Limit report to a single job.")
    r.add_argument("--last", type=int, default=50, metavar="N", help="Number of recent runs to include.")

    # digest
    d = sub.add_parser("digest", help="Send a digest email and exit.")
    d.add_argument("--hours", type=int, default=24, help="History window in hours.")

    return p


def cmd_watch(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    init_db(args.db)
    run_watch_loop(cfg, args.db, interval=args.interval)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    init_db(args.db)
    jobs = [j for j in cfg.jobs if args.job is None or j.name == args.job]
    if not jobs:
        print(f"No jobs found matching: {args.job}", file=sys.stderr)
        return 1
    lines: List[str] = []
    for job in jobs:
        records = load_records(args.db, job.name)[: args.last]
        summary = build_summary(job, records)
        lines.append(str(summary))
    print("\n".join(lines))
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    if cfg.alert is None:
        print("No alert configuration found; cannot send digest.", file=sys.stderr)
        return 1
    init_db(args.db)
    result = send_digest(cfg, cfg.alert, args.db, period_hours=args.hours)
    status = "sent" if result.sent else "skipped (no records)"
    print(f"Digest {status} — {result.jobs_included} job(s) included.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level))

    if args.command == "watch":
        return cmd_watch(args)
    if args.command == "report":
        return cmd_report(args)
    if args.command == "digest":
        return cmd_digest(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
