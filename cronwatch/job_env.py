"""Per-job environment variable management.

Provides helpers to build a merged environment for a job, combining
process-level defaults with per-job overrides defined in config.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

from cronwatch.config import JobConfig


def base_env() -> Dict[str, str]:
    """Return a copy of the current process environment."""
    return dict(os.environ)


def build_job_env(
    job: JobConfig,
    extra: Optional[Dict[str, str]] = None,
    inherit: bool = True,
) -> Dict[str, str]:
    """Build the environment dict for *job*.

    Args:
        job:     Job configuration (may carry an ``env`` mapping).
        extra:   Additional key/value pairs applied last (highest priority).
        inherit: When *True* (default) start from the process environment;
                 when *False* start from an empty dict.

    Returns:
        A new dict ready to be passed as *env* to ``subprocess``.
    """
    env: Dict[str, str] = base_env() if inherit else {}

    job_env: Dict[str, str] = getattr(job, "env", None) or {}
    env.update({str(k): str(v) for k, v in job_env.items()})

    if extra:
        env.update({str(k): str(v) for k, v in extra.items()})

    return env


def redact_env(
    env: Dict[str, str],
    sensitive_keys: Optional[list[str]] = None,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by ``***``.

    Keys are matched case-insensitively against *sensitive_keys*.
    Defaults cover common secret-bearing variable names.
    """
    defaults = [
        "password", "passwd", "secret", "token", "api_key",
        "apikey", "auth", "credential", "private_key",
    ]
    blocked = {k.lower() for k in (sensitive_keys or defaults)}
    return {
        k: ("***" if any(b in k.lower() for b in blocked) else v)
        for k, v in env.items()
    }
