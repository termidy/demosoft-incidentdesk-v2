"""The same alert often fires several times. Drafts for one service with the same fingerprint, or the same title,
within ten minutes of the first one are duplicates."""

from datetime import timedelta

import pytz

from incidentdesk.ingest.webhook import Draft

WINDOW = timedelta(minutes=10)


def dedupe(drafts: list[Draft]) -> tuple[list[Draft], list[Draft]]:
    """(kept, duplicates), in time order."""
    kept: list[Draft] = []
    duplicates: list[Draft] = []
    for draft in sorted(drafts, key=lambda d: d.opened_at.astimezone(pytz.utc)):
        first = next(
            (k for k in kept
             if k.service_slug == draft.service_slug
             and (k.fingerprint == draft.fingerprint or k.title.lower() == draft.title.lower())
             and draft.opened_at - k.opened_at <= WINDOW),
            None,
        )
        (duplicates if first else kept).append(draft)
    return kept, duplicates
