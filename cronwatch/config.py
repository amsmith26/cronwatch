"""Configuration loading for cronwatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class JobConfig:
    name: str
    schedule: str                        # cron expression
    command: str
    grace_seconds: int = 60
    timeout_seconds: Optional[int] = None


@dataclass
class AlertConfig:
    email: Optional[str] = None
    from_address: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    on_failure: bool = True
    on_missed: bool = True


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    log_level: str = "INFO"
    state_dir: str = "/var/lib/cronwatch"


def _parse_job(raw: dict) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        schedule=raw["schedule"],
        command=raw["command"],
        grace_seconds=int(raw.get("grace_seconds", 60)),
        timeout_seconds=raw.get("timeout_seconds"),
    )


def _parse_alert(raw: dict) -> AlertConfig:
    return AlertConfig(
        email=raw.get("email"),
        from_address=raw.get("from_address"),
        smtp_host=raw.get("smtp_host"),
        smtp_port=raw.get("smtp_port"),
        on_failure=bool(raw.get("on_failure", True)),
        on_missed=bool(raw.get("on_missed", True)),
    )


def load_config(path: str | Path) -> CronwatchConfig:
    """Load and validate a cronwatch YAML config file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    with p.open() as fh:
        raw = yaml.safe_load(fh) or {}

    jobs = [_parse_job(j) for j in raw.get("jobs", [])]
    alert = _parse_alert(raw.get("alert", {}))

    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        log_level=raw.get("log_level", "INFO"),
        state_dir=raw.get("state_dir", "/var/lib/cronwatch"),
    )
