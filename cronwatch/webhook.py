"""Webhook alert dispatch — sends JSON payloads to configured HTTP endpoints."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from cronwatch.tracker import RunRecord, RunStatus

log = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 10  # seconds


def _build_payload(job_name: str, record: RunRecord) -> dict:
    """Build a JSON-serialisable dict describing the run event."""
    return {
        "job": job_name,
        "status": record.status.value,
        "started_at": record.started_at.isoformat() if record.started_at else None,
        "finished_at": record.finished_at.isoformat() if record.finished_at else None,
        "exit_code": record.exit_code,
        "duration_seconds": (
            (record.finished_at - record.started_at).total_seconds()
            if record.started_at and record.finished_at
            else None
        ),
        "error": record.error,
    }


def send_webhook(
    url: str,
    job_name: str,
    record: RunRecord,
    timeout: int = _DEFAULT_TIMEOUT,
    secret: Optional[str] = None,
) -> bool:
    """POST a JSON payload to *url*.  Returns True on HTTP 2xx, False otherwise."""
    if not url:
        log.debug("send_webhook: no URL configured, skipping")
        return False

    payload = _build_payload(job_name, record)
    body = json.dumps(payload).encode()

    headers = {"Content-Type": "application/json"}
    if secret:
        import hashlib
        import hmac

        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers["X-Cronwatch-Signature"] = f"sha256={sig}"

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            log.debug("send_webhook: %s responded %s", url, status)
            return 200 <= status < 300
    except urllib.error.HTTPError as exc:
        log.warning("send_webhook: HTTP %s from %s — %s", exc.code, url, exc.reason)
        return False
    except Exception as exc:  # network errors, timeouts, etc.
        log.warning("send_webhook: failed to reach %s — %s", url, exc)
        return False
