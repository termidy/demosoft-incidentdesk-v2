"""The examples table of docs/priority-rules.md, as tests."""

from incidentdesk.priority import compute_priority
from tests.conftest import chicago


def test_major_customer_facing_tuesday_afternoon_is_p1():
    assert compute_priority("major", True, chicago(2026, 10, 13, 14, 0)) == "P1"


def test_major_customer_facing_tuesday_night_is_p1():
    assert compute_priority("major", True, chicago(2026, 10, 13, 23, 30)) == "P1"


def test_major_customer_facing_saturday_morning_is_p1():
    assert compute_priority("major", True, chicago(2026, 10, 17, 10, 0)) == "P1"
