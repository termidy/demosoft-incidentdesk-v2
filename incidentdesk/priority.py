"""The priority of a new incident (docs/priority-rules.md)."""

from datetime import datetime

SEVERITY_START = {"critical": 1, "major": 2, "minor": 3, "cosmetic": 4}


def compute_priority(severity: str, customer_facing: bool, opened_at: datetime, in_maintenance: bool = False) -> str:
    level = SEVERITY_START[severity]
    if customer_facing:
        level -= 1
    if in_maintenance:
        level += 1
    return f"P{min(max(level, 1), 4)}"
