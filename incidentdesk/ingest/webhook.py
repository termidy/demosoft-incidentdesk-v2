"""Alerts from the monitoring system arrive as webhooks and become incident drafts."""

from dataclasses import dataclass
from datetime import datetime

import pytz

SEVERITY_MAP = {"page": "critical", "high": "major", "warning": "minor", "info": "cosmetic"}


@dataclass(frozen=True)
class Draft:
    service_slug: str
    title: str
    severity: str
    opened_at: datetime
    source: str
    fingerprint: str


def from_monitoring(payload: dict) -> Draft:
    """Monitoring sends `fired_at` as Unix seconds (UTC) and its own severity names."""
    labels = payload["labels"]
    return Draft(
        service_slug=labels["service"],
        title=payload["summary"].strip(),
        severity=SEVERITY_MAP[payload["severity"]],
        opened_at=datetime.fromtimestamp(payload["fired_at"], tz=pytz.utc),
        source="monitoring",
        fingerprint=payload["fingerprint"],
    )
