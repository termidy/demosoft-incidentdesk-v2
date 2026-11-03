"""The audit trail of changes made through the API: one line per change, UTC time first."""

from dataclasses import dataclass
from datetime import datetime

import pytz


@dataclass(frozen=True)
class AuditEntry:
    at: datetime
    actor: str
    action: str
    target: str

    def line(self) -> str:
        return f"{self.at.astimezone(pytz.utc):%Y-%m-%dT%H:%M:%SZ} {self.actor} {self.action} {self.target}"


def entry(actor: str, action: str, target: str, at: datetime) -> AuditEntry:
    if at.tzinfo is None:
        raise ValueError("audit times must be timezone-aware")
    return AuditEntry(at.astimezone(pytz.utc), actor, action, target)
