"""Pre/post execution hooks for cron jobs."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HookConfig:
    pre: List[str] = field(default_factory=list)
    post_success: List[str] = field(default_factory=list)
    post_failure: List[str] = field(default_factory=list)


@dataclass
class HookResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _run_hook(command: str, timeout: int = 30) -> HookResult:
    """Run a single shell hook command and return its result."""
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return HookResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
        )
    except subprocess.TimeoutExpired:
        return HookResult(command=command, returncode=-1, stdout="", stderr="timeout")
    except Exception as exc:  # noqa: BLE001
        return HookResult(command=command, returncode=-1, stdout="", stderr=str(exc))


def run_hooks(commands: List[str], timeout: int = 30) -> List[HookResult]:
    """Run a list of hook commands sequentially, stopping on first failure."""
    results: List[HookResult] = []
    for cmd in commands:
        result = _run_hook(cmd, timeout=timeout)
        results.append(result)
        if not result.ok:
            break
    return results


def parse_hook_config(raw: Optional[dict]) -> HookConfig:
    """Build a HookConfig from a raw YAML dict (or None)."""
    if not raw:
        return HookConfig()

    def _as_list(val) -> List[str]:
        if val is None:
            return []
        if isinstance(val, str):
            return [val]
        return list(val)

    return HookConfig(
        pre=_as_list(raw.get("pre")),
        post_success=_as_list(raw.get("post_success")),
        post_failure=_as_list(raw.get("post_failure")),
    )


def hooks_summary(cfg: HookConfig) -> str:
    """Return a human-readable summary of configured hooks."""
    parts = []
    if cfg.pre:
        parts.append(f"pre({len(cfg.pre)}): {', '.join(cfg.pre)}")
    if cfg.post_success:
        parts.append(f"post_success({len(cfg.post_success)}): {', '.join(cfg.post_success)}")
    if cfg.post_failure:
        parts.append(f"post_failure({len(cfg.post_failure)}): {', '.join(cfg.post_failure)}")
    return "; ".join(parts) if parts else "no hooks configured"
