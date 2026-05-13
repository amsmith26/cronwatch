"""CLI sub-commands for inspecting job labels."""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.job_labels import collect_label_keys, jobs_with_label, label_index


def add_labels_subparser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("labels", help="Inspect job labels")
    sp = p.add_subparsers(dest="labels_cmd")

    ls = sp.add_parser("list", help="List all label keys")
    ls.set_defaults(labels_func=_cmd_list)

    show = sp.add_parser("show", help="Show jobs matching a label")
    show.add_argument("key", help="Label key")
    show.add_argument("value", nargs="?", default=None, help="Label value (optional)")
    show.set_defaults(labels_func=_cmd_show)

    idx = sp.add_parser("index", help="Print full label index")
    idx.set_defaults(labels_func=_cmd_index)

    p.set_defaults(labels_func=_cmd_default)


def cmd_labels(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    func = getattr(args, "labels_func", _cmd_default)
    return func(args, cfg)


def _cmd_default(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    print("Usage: cronwatch labels {list,show,index}", file=sys.stderr)
    return 1


def _cmd_list(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    keys = collect_label_keys(cfg.jobs)
    if not keys:
        print("(no labels defined)")
    else:
        for k in keys:
            print(k)
    return 0


def _cmd_show(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    matches = jobs_with_label(cfg.jobs, args.key, args.value)
    if not matches:
        print("(no jobs match)")
        return 0
    for job in matches:
        val = (job.labels or {}).get(args.key, "")
        print(f"{job.name}  {args.key}={val}")
    return 0


def _cmd_index(args: argparse.Namespace, cfg: CronwatchConfig) -> int:
    idx = label_index(cfg.jobs)
    if not idx:
        print("(no labels defined)")
        return 0
    for key in sorted(idx):
        for val in sorted(idx[key]):
            names = ", ".join(j.name for j in idx[key][val])
            print(f"{key}={val}: {names}")
    return 0
