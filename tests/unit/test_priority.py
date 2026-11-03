import pytz

from incidentdesk.priority import compute_priority
from tests.conftest import chicago


def test_severity_sets_the_starting_priority():
    at = chicago(2026, 10, 13, 14, 0)
    assert [compute_priority(s, False, at) for s in ("critical", "major", "minor", "cosmetic")] == ["P1", "P2", "P3", "P4"]


def test_customer_facing_is_raised_one_level_during_the_day():
    assert compute_priority("major", True, chicago(2026, 10, 13, 14, 0)) == "P1"


def test_p1_stays_p1():
    assert compute_priority("critical", True, chicago(2026, 10, 13, 14, 0)) == "P1"


def test_maintenance_lowers_one_level():
    assert compute_priority("minor", False, chicago(2026, 10, 13, 14, 0), in_maintenance=True) == "P4"
    assert compute_priority("cosmetic", False, chicago(2026, 10, 13, 14, 0), in_maintenance=True) == "P4"


def test_time_is_compared_in_the_service_time_zone():
    at = chicago(2026, 10, 13, 14, 0).astimezone(pytz.utc)  # 19:00 UTC
    assert compute_priority("major", True, at) == "P1"
