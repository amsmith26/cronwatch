"""Configuration loader for cronwatch."""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str
    timeout: int = 3600
    alert_email: Optional[str] = None
    max_retries: int = 0


@dataclass
class AlertConfig:
    email: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    log_file: str = "/var/log/cronwatch.log"
    state_dir: str = "/var/lib/cronwatch"
    check_interval: int = 60


def load_config(path: str) -> CronwatchConfig:
    """Load and parse a YAML configuration file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping")

    alert_raw = raw.get("alerts", {})
    alerts = AlertConfig(
        email=alert_raw.get("email"),
        smtp_host=alert_raw.get("smtp_host", "localhost"),
        smtp_port=int(alert_raw.get("smtp_port", 25)),
        smtp_user=alert_raw.get("smtp_user"),
        smtp_password=alert_raw.get("smtp_password"),
    )

    jobs = []
    for job_raw in raw.get("jobs", []):
        jobs.append(JobConfig(
            name=job_raw["name"],
            schedule=job_raw["schedule"],
            timeout=int(job_raw.get("timeout", 3600)),
            alert_email=job_raw.get("alert_email"),
            max_retries=int(job_raw.get("max_retries", 0)),
        ))

    return CronwatchConfig(
        jobs=jobs,
        alerts=alerts,
        log_file=raw.get("log_file", "/var/log/cronwatch.log"),
        state_dir=raw.get("state_dir", "/var/lib/cronwatch"),
        check_interval=int(raw.get("check_interval", 60)),
    )
