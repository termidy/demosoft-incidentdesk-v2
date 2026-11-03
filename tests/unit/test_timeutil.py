from datetime import datetime

import pytz

from incidentdesk import timeutil


def test_parse_utc_reads_z_and_offsets():
    assert timeutil.parse_utc("2026-10-13T19:00:00Z") == pytz.utc.localize(datetime(2026, 10, 13, 19, 0))
    assert timeutil.parse_utc("2026-10-13T14:00:00-05:00") == pytz.utc.localize(datetime(2026, 10, 13, 19, 0))


def test_parse_utc_takes_a_naive_string_as_utc():
    assert timeutil.parse_utc("2026-10-13T19:00:00").tzinfo is not None


def test_now_can_be_pinned(monkeypatch):
    monkeypatch.setenv("INCIDENTDESK_NOW", "2026-10-15T15:00:00Z")
    assert timeutil.now() == pytz.utc.localize(datetime(2026, 10, 15, 15, 0))


def test_local_datetime_handles_daylight_saving():
    before = timeutil.local_datetime(2026, 10, 31, 12, 0)
    after = timeutil.local_datetime(2026, 11, 2, 12, 0)
    assert before.utcoffset().total_seconds() == -5 * 3600
    assert after.utcoffset().total_seconds() == -6 * 3600


def test_business_hours():
    assert timeutil.is_business_hours(timeutil.local_datetime(2026, 10, 13, 9, 0))
    assert not timeutil.is_business_hours(timeutil.local_datetime(2026, 10, 13, 18, 0))
    assert not timeutil.is_business_hours(timeutil.local_datetime(2026, 10, 17, 12, 0))
