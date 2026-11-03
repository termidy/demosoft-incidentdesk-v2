"""The weekly report: Monday to Sunday in the service time zone."""

from datetime import date, timedelta

import pytz

from incidentdesk.config import settings
from incidentdesk.models import Incident
from incidentdesk.reports.daily import daily_report


def week_of(day: date) -> list[date]:
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=n) for n in range(7)]


def weekly_report(incidents: list[Incident], any_day: date) -> dict:
    days = [daily_report(incidents, d) for d in week_of(any_day)]
    tz = pytz.timezone(settings().timezone)
    return {
        "week": f"{days[0]['day']}..{days[-1]['day']}",
        "timezone": tz.zone,
        "opened": sum(d["opened"] for d in days),
        "busiest_day": max(days, key=lambda d: d["opened"])["day"],
        "days": days,
    }
