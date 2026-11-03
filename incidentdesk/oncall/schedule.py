"""On-call rotations. Each rotation hands over every Monday at 10:00 in its own time zone."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pytz


@dataclass(frozen=True)
class Rotation:
    name: str
    timezone: str
    engineers: tuple[str, ...]


ROTATIONS = {
    "amer": Rotation("amer", "America/Chicago", ("a.reyes", "j.morgan", "k.osei", "l.chen")),
    "emea": Rotation("emea", "Europe/Lisbon", ("m.santos", "p.novak", "r.haddad")),
    "apac": Rotation("apac", "Asia/Singapore", ("s.tan", "d.kumar", "y.sato")),
}

FIRST_MONDAY = date(2026, 1, 5)  # week 0 of every rotation
HANDOFF_TIME = time(10, 0)


def handoff_before(rotation: Rotation, at: datetime) -> datetime:
    """The last handoff of this rotation at or before `at`."""
    tz = pytz.timezone(rotation.timezone)
    local = at.astimezone(tz)
    monday = local.date() - timedelta(days=local.weekday())
    handoff = tz.localize(datetime.combine(monday, HANDOFF_TIME))
    if handoff > local:
        handoff = tz.localize(datetime.combine(monday - timedelta(days=7), HANDOFF_TIME))
    return handoff


def on_call(rotation_name: str, at: datetime) -> str:
    rotation = ROTATIONS[rotation_name]
    week = (handoff_before(rotation, at).date() - FIRST_MONDAY).days // 7
    return rotation.engineers[week % len(rotation.engineers)]
