from datetime import date, datetime, timedelta

import pytz

from incidentdesk.statuspage.history import downtime_by_day, uptime_percent
from incidentdesk.statuspage.publisher import status_entry
from tests.conftest import make_incident, make_service


def test_only_customer_facing_p1_and_p2_are_public():
    assert status_entry(make_incident(priority="P3")) is None
    assert status_entry(make_incident(service=make_service(customer_facing=False))) is None
    assert status_entry(make_incident())["since"] == "2026-10-13 19:00 UTC"


def test_downtime_is_split_at_utc_midnight():
    opened = pytz.utc.localize(datetime(2026, 10, 13, 23, 30))
    incident = make_incident(severity="critical", opened_at=opened, resolved_at=opened + timedelta(hours=1))
    history = downtime_by_day([incident], "login-service", date(2026, 10, 15))
    assert history[date(2026, 10, 13)] == timedelta(minutes=30)
    assert history[date(2026, 10, 14)] == timedelta(minutes=30)
    assert uptime_percent(history) < 100
