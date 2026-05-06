"""Alert dispatching for cronwatch — sends notifications on job failures or missed runs."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from cronwatch.config import AlertConfig
from cronwatch.tracker import RunRecord, RunStatus

logger = logging.getLogger(__name__)


def _build_subject(record: RunRecord, reason: str) -> str:
    return f"[cronwatch] {reason}: {record.job_name}"


def _build_body(record: RunRecord, reason: str) -> str:
    lines = [
        f"Job:       {record.job_name}",
        f"Reason:    {reason}",
        f"Started:   {record.started_at}",
    ]
    if record.finished_at:
        lines.append(f"Finished:  {record.finished_at}")
    if record.exit_code is not None:
        lines.append(f"Exit code: {record.exit_code}")
    if record.output:
        lines.append(f"\nOutput:\n{record.output}")
    return "\n".join(lines)


def send_email_alert(
    cfg: AlertConfig,
    record: RunRecord,
    reason: str,
    smtp_factory=None,
) -> bool:
    """Send an e-mail alert.  Returns True on success."""
    if not cfg.email:
        logger.debug("No email recipient configured; skipping e-mail alert.")
        return False

    msg = EmailMessage()
    msg["Subject"] = _build_subject(record, reason)
    msg["From"] = cfg.from_address or "cronwatch@localhost"
    msg["To"] = cfg.email
    msg.set_content(_build_body(record, reason))

    host = cfg.smtp_host or "localhost"
    port = cfg.smtp_port or 25

    try:
        factory = smtp_factory or smtplib.SMTP
        with factory(host, port) as smtp:
            smtp.send_message(msg)
        logger.info("Alert e-mail sent to %s for job '%s'.", cfg.email, record.job_name)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send alert e-mail: %s", exc)
        return False


def dispatch_alert(
    cfg: AlertConfig,
    record: RunRecord,
    reason: Optional[str] = None,
    smtp_factory=None,
) -> None:
    """Determine alert reason and dispatch all configured channels."""
    if reason is None:
        if record.status == RunStatus.FAILED:
            reason = "Job failed"
        elif record.status == RunStatus.MISSED:
            reason = "Job missed"
        else:
            reason = "Alert"

    send_email_alert(cfg, record, reason, smtp_factory=smtp_factory)
