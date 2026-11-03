"""Mean time to acknowledge and to resolve, per service."""

from collections import defaultdict
from datetime import datetime, timedelta

import pytz

from incidentdesk.models import Incident


def _mean(values: list[timedelta]) -> float | None:
    return round(sum(v.total_seconds() for v in values) / len(values) / 60, 1) if values else None


def mttr_by_service(incidents: list[Incident], since: datetime) -> dict[str, dict]:
    since = since.astimezone(pytz.utc)
    ack, res = defaultdict(list), defaultdict(list)
    for incident in incidents:
        if incident.opened_at < since:
            continue
        slug = incident.service.slug
        if incident.acknowledged_at:
            ack[slug].append(incident.acknowledged_at - incident.opened_at)
        if incident.resolved_at:
            res[slug].append(incident.resolved_at - incident.opened_at - timedelta(seconds=incident.waiting_seconds))
    slugs = sorted(set(ack) | set(res))
    return {s: {"mtta_minutes": _mean(ack[s]), "mttr_minutes": _mean(res[s])} for s in slugs}
