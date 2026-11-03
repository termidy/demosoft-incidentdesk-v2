"""Who responds first to a new incident (docs/routing.md)."""

from datetime import datetime

from incidentdesk.models import Service
from incidentdesk.oncall.schedule import on_call
from incidentdesk.timeutil import is_business_hours


def first_responders(service: Service, priority: str, opened_at: datetime) -> list[str]:
    if is_business_hours(opened_at):
        responders = [f"team:{service.team}"]
        if priority == "P1":
            responders.append(f"oncall:{on_call(service.rotation, opened_at)}")
    else:
        responders = [f"oncall:{on_call(service.rotation, opened_at)}"]
    return responders
