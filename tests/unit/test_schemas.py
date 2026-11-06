import pytest
from pydantic import ValidationError

from incidentdesk.schemas import IncidentIn


@pytest.mark.parametrize("title", ["   ", "x" * 201])
def test_incident_title_must_have_one_to_200_non_whitespace_characters(title):
    with pytest.raises(ValidationError):
        IncidentIn(service="login-service", title=title, severity="major")


def test_incident_title_is_trimmed_before_checking_its_length():
    title = " " + "x" * 200 + " "
    incident = IncidentIn(service="login-service", title=title, severity="major")
    assert incident.title == "x" * 200
