"""Incidents reported by email to incidents@demosoft.example.

Customers write the time the way they see it. The support form adds a `Reported-Time` header in the form
`2026-10-14 23:30` and a `Reported-TZ` header with the customer's time zone; old clients send no `Reported-TZ`.
"""

from datetime import datetime, timezone
from email.message import Message
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from incidentdesk.config import settings
from incidentdesk.ingest.webhook import Draft

KEYWORDS = {"down": "critical", "outage": "critical", "error": "major", "slow": "minor"}


def _localize(wall_time: datetime, tz: ZoneInfo) -> datetime:
    local = wall_time.replace(tzinfo=tz)
    later = wall_time.replace(tzinfo=tz, fold=1)
    if (
        local.utcoffset() != later.utcoffset()
        and later.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) == wall_time
    ):
        return later
    return local


def reported_at(msg: Message) -> datetime:
    if msg.get("Reported-Time"):
        tz = ZoneInfo(msg.get("Reported-TZ") or settings().timezone)
        naive = datetime.strptime(msg["Reported-Time"], "%Y-%m-%d %H:%M")
        return _localize(naive, tz).astimezone(timezone.utc)
    return parsedate_to_datetime(msg["Date"]).astimezone(timezone.utc)


def guess_severity(subject: str) -> str:
    words = subject.lower().split()
    for keyword, severity in KEYWORDS.items():
        if keyword in words:
            return severity
    return "minor"


def from_email(msg: Message, service_slug: str) -> Draft:
    subject = " ".join(msg["Subject"].split())
    return Draft(service_slug, subject, guess_severity(subject), reported_at(msg), "email", msg["Message-ID"])
