import pytz

from incidentdesk.routing import first_responders
from tests.conftest import chicago, make_service


def test_team_responds_during_business_hours():
    assert first_responders(make_service(), "P2", chicago(2026, 10, 13, 10, 0)) == ["team:identity"]


def test_on_call_responds_at_night():
    responders = first_responders(make_service(), "P2", chicago(2026, 10, 13, 23, 30))
    assert len(responders) == 1 and responders[0].startswith("oncall:")


def test_on_call_responds_at_the_weekend():
    assert first_responders(make_service(), "P3", chicago(2026, 10, 17, 11, 0))[0].startswith("oncall:")


def test_p1_pages_on_call_during_the_day_too():
    responders = first_responders(make_service(), "P1", chicago(2026, 10, 13, 10, 0))
    assert responders[0] == "team:identity" and responders[1].startswith("oncall:")


def test_business_hours_end_at_six_in_the_service_time_zone():
    six_pm = chicago(2026, 10, 13, 18, 0).astimezone(pytz.utc)
    assert first_responders(make_service(), "P2", six_pm)[0].startswith("oncall:")
