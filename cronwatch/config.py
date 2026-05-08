"""Configuration loading for cronwatch.

Extends the existing config module to support an optional *tags* field on
JobConfig so that tag-based filtering works out of the box.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class JobConfig:
    name: str
    schedule: str
    command: str
    grace_seconds: int = 60
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    smtp_host: str = "localhost"
    smtp_port: int = 25
    from_addr: str = "cronwatch@localhost"
    to_addrs: List[str] = field(default_factory=list)
    use_tls: bool = False
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    db_path: str = "cronwatch.db"
    check_interval: int = 60


def _parse_job(raw: Dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        schedule=raw["schedule"],
        command=raw.get("command", ""),
        grace_seconds=int(raw.get("grace_seconds", 60)),
        tags=list(raw.get("tags") or []),
    )


def _parse_alert(raw: Dict[str, Any]) -> AlertConfig:
    return AlertConfig(
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=int(raw.get("smtp_port", 25)),
        from_addr=raw.get("from_addr", "cronwatch@localhost"),
        to_addrs=list(raw.get("to_addrs") or []),
        use_tls=bool(raw.get("use_tls", False)),
        username=raw.get("username"),
        password=raw.get("password"),
    )


def load_config(path: str) -> CronwatchConfig:
    """Load and parse a YAML configuration file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as fh:
        raw = yaml.safe_load(fh) or {}

    jobs = [_parse_job(j) for j in raw.get("jobs") or []]
    alert = _parse_alert(raw.get("alert") or {})
    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        db_path=raw.get("db_path", "cronwatch.db"),
        check_interval=int(raw.get("check_interval", 60)),
    )
