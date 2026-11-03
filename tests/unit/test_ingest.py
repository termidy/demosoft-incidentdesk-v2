from datetime import datetime
from email.message import Message

import pytz

from incidentdesk.ingest.dedupe import dedupe
from incidentdesk.ingest.email_parser import from_email
from incidentdesk.ingest.webhook import from_monitoring

PAYLOAD = {"labels": {"service": "checkout-api"}, "summary": " Checkout API: error rate above 5% ", "severity": "high",
           "fired_at": 1792004400, "fingerprint": "a1b2"}


def test_monitoring_alert_becomes_a_draft():
    draft = from_monitoring(PAYLOAD)
    assert draft.severity == "major" and draft.title == "Checkout API: error rate above 5%"
    assert draft.opened_at == pytz.utc.localize(datetime(2026, 10, 14, 19, 0))


def test_email_time_uses_the_customer_time_zone():
    msg = Message()
    msg["Subject"] = "Login   is down"
    msg["Reported-Time"] = "2026-10-14 23:30"
    msg["Reported-TZ"] = "Europe/Lisbon"
    msg["Message-ID"] = "<m1@example>"
    draft = from_email(msg, "login-service")
    assert draft.title == "Login is down" and draft.severity == "critical"
    assert draft.opened_at == pytz.utc.localize(datetime(2026, 10, 14, 22, 30))


def test_repeated_alert_within_ten_minutes_is_a_duplicate():
    first = from_monitoring(PAYLOAD)
    again = from_monitoring({**PAYLOAD, "fired_at": PAYLOAD["fired_at"] + 240})
    later = from_monitoring({**PAYLOAD, "fired_at": PAYLOAD["fired_at"] + 3600})
    kept, duplicates = dedupe([later, again, first])
    assert kept == [first, later] and duplicates == [again]
