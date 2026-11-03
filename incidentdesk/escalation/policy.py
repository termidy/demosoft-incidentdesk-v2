"""Escalation steps: who is paged, and how long after opening, while nobody has acknowledged."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Step:
    after: timedelta
    target: str  # oncall, team-lead, engineering-manager


POLICY = {
    "P1": (Step(timedelta(0), "oncall"), Step(timedelta(minutes=10), "team-lead"), Step(timedelta(minutes=20), "engineering-manager")),
    "P2": (Step(timedelta(0), "oncall"), Step(timedelta(minutes=30), "team-lead")),
    "P3": (Step(timedelta(0), "team"),),
    "P4": (Step(timedelta(0), "team"),),
}


def steps_for(priority: str) -> tuple[Step, ...]:
    return POLICY[priority]
