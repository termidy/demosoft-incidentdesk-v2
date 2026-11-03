from datetime import datetime

import pytz

from incidentdesk.notify.chat import opened_message
from incidentdesk.notify.digest import next_digest_at
from incidentdesk.notify.email import incident_email
from tests.conftest import chicago, make_incident


def test_email_shows_the_service_time():
    email = incident_email(make_incident(), ["oncall@demosoft.example"])
    assert email.subject == "[P2] INC-4821 Login fails for some customers"
    assert "Opened: 2026-10-13 14:00 CDT" in email.body


def test_chat_message_shows_utc():
    assert "opened 19:00 UTC" in opened_message(make_incident(), ["team:identity"])


def test_digest_goes_out_at_eight_in_the_recipient_time_zone():
    singapore = pytz.timezone("Asia/Singapore")
    at = next_digest_at("Asia/Singapore", chicago(2026, 10, 13, 14, 0))
    assert at == singapore.localize(datetime(2026, 10, 14, 8, 0))
