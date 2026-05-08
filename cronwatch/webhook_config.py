"""Webhook configuration helpers — parsing and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WebhookConfig:
    url: str
    secret: Optional[str] = None
    timeout: int = 10
    on_statuses: List[str] = field(default_factory=lambda: ["failure", "missed"])

    def wants_status(self, status: str) -> bool:
        """Return True if this webhook should fire for *status*."""
        return status in self.on_statuses


def parse_webhook_configs(raw: object) -> List[WebhookConfig]:
    """Parse the ``webhooks`` section of a config dict into WebhookConfig objects.

    Accepts either a single mapping or a list of mappings.
    """
    if not raw:
        return []

    entries = raw if isinstance(raw, list) else [raw]
    configs: List[WebhookConfig] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"webhook entry must be a mapping, got {type(entry)}")
        url = entry.get("url", "").strip()
        if not url:
            raise ValueError("webhook entry missing required 'url' field")
        configs.append(
            WebhookConfig(
                url=url,
                secret=entry.get("secret"),
                timeout=int(entry.get("timeout", 10)),
                on_statuses=list(entry.get("on_statuses", ["failure", "missed"])),
            )
        )
    return configs
