from datetime import datetime, timedelta, timezone

from incidentdesk.maintenance.windows import in_maintenance, weekly_window
from incidentdesk.models import MaintenanceWindow
from tests.conftest import chicago


def test_weekly_window_is_sunday_two_to_four_local():
    start, end = weekly_window(chicago(2026, 10, 14, 12, 0))
    assert start == chicago(2026, 10, 11, 2, 0) and end == chicago(2026, 10, 11, 4, 0)


def test_weekly_window_keeps_its_duration_across_the_spring_dst_gap():
    start, end = weekly_window(chicago(2026, 3, 8, 12, 0))
    assert end.astimezone(timezone.utc) - start.astimezone(timezone.utc) == timedelta(hours=2)


def test_inside_the_weekly_window():
    assert in_maintenance(1, chicago(2026, 10, 11, 3, 0), [])
    assert not in_maintenance(1, chicago(2026, 10, 11, 4, 0), [])


def test_one_off_window_applies_only_to_its_service():
    window = MaintenanceWindow(service_id=2, starts_at=datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc),
                               ends_at=datetime(2026, 10, 13, 20, 0, tzinfo=timezone.utc), reason="Database upgrade")
    assert in_maintenance(2, chicago(2026, 10, 13, 14, 30), [window])
    assert not in_maintenance(1, chicago(2026, 10, 13, 14, 30), [window])
