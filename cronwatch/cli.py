"""Command-line interface for cronwatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.reporter import generate_report
from cronwatch.tracker import JobTracker
from cronwatch.watcher import run_watch_loop


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor cron job execution and alert on failures.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # watch sub-command
    watch_p = sub.add_parser("watch", help="Start the monitoring daemon.")
    watch_p.add_argument(
        "-c", "--config", default="cronwatch.yaml", metavar="FILE",
        help="Path to configuration file (default: cronwatch.yaml).",
    )
    watch_p.add_argument(
        "--interval", type=int, default=60, metavar="SECONDS",
        help="Poll interval in seconds (default: 60).",
    )

    # report sub-command
    report_p = sub.add_parser("report", help="Print a summary report and exit.")
    report_p.add_argument(
        "-c", "--config", default="cronwatch.yaml", metavar="FILE",
        help="Path to configuration file.",
    )

    return parser


def cmd_watch(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    tracker = JobTracker(cfg.jobs)
    try:
        run_watch_loop(cfg, tracker, interval=args.interval)
    except KeyboardInterrupt:
        print("\ncronwatch stopped.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    tracker = JobTracker(cfg.jobs)
    report = generate_report(tracker)
    print(report.as_text())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "watch":
        return cmd_watch(args)
    if args.command == "report":
        return cmd_report(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
