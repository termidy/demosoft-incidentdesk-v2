from datetime import date, timedelta

import pytz

from incidentdesk.reports.daily import daily_report, day_bounds
from incidentdesk.reports.mttr import mttr_by_service
from incidentdesk.reports.weekly import weekly_report
from tests.conftest import chicago, make_incident


def test_a_local_day_is_25_hours_when_clocks_go_back():
    start, end = day_bounds(date(2026, 11, 1))
    assert end - start == timedelta(hours=25)
    assert start.tzinfo == pytz.utc


def test_daily_report_counts_by_local_day():
    late = make_incident(key="INC-1", opened_at=chicago(2026, 10, 13, 23, 30))
    early = make_incident(key="INC-2", opened_at=chicago(2026, 10, 14, 0, 30), priority="P3")
    report = daily_report([late, early], date(2026, 10, 13))
    assert report["opened"] == 1 and report["by_priority"] == {"P2": 1}


def test_weekly_report_runs_monday_to_sunday():
    report = weekly_report([make_incident(opened_at=chicago(2026, 10, 18, 22, 0))], date(2026, 10, 14))
    assert report["week"] == "2026-10-12..2026-10-18" and report["opened"] == 1


def test_mttr_leaves_out_waiting_time():
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(opened_at=opened, acknowledged_at=opened + timedelta(minutes=10),
                             resolved_at=opened + timedelta(minutes=70), waiting_seconds=600)
    assert mttr_by_service([incident], opened - timedelta(days=1)) == {"login-service": {"mtta_minutes": 10.0, "mttr_minutes": 60.0}}
