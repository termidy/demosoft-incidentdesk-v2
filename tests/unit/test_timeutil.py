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


def test_to_local_handles_spring_forward():
    chicago = pytz.timezone("America/Chicago")
    before = timeutil.to_local(timeutil.parse_utc("2026-03-08T07:59:59Z"))
    after = timeutil.to_local(timeutil.parse_utc("2026-03-08T08:00:00Z"))

    assert before == chicago.localize(datetime(2026, 3, 8, 1, 59, 59), is_dst=True)
    assert after == chicago.localize(datetime(2026, 3, 8, 3, 0, 0), is_dst=True)


def test_to_local_handles_fall_back():
    chicago = pytz.timezone("America/Chicago")
    before = timeutil.to_local(timeutil.parse_utc("2026-11-01T06:59:59Z"))
    after = timeutil.to_local(timeutil.parse_utc("2026-11-01T07:00:00Z"))

    assert before == chicago.localize(datetime(2026, 11, 1, 1, 59, 59), is_dst=True)
    assert after == chicago.localize(datetime(2026, 11, 1, 1, 0, 0), is_dst=False)


def test_business_hours():
    assert timeutil.is_business_hours(timeutil.local_datetime(2026, 10, 13, 9, 0))
    assert not timeutil.is_business_hours(timeutil.local_datetime(2026, 10, 13, 18, 0))
    assert not timeutil.is_business_hours(timeutil.local_datetime(2026, 10, 17, 12, 0))
