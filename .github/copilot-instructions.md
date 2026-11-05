# Instructions for Copilot in incidentdesk

- Every change that users can notice adds one line to CHANGELOG.md
  under "## Unreleased", in plain words for on-call engineers.

## Moving from pytz to zoneinfo (#24)

- In every Python file you change, replace pytz with zoneinfo: `ZoneInfo("America/Chicago")` instead of `pytz.timezone("America/Chicago")`, `timezone.utc` instead of `pytz.utc`.
- `tz.localize(dt)` becomes `dt.replace(tzinfo=tz)`, and `tz.normalize(...)` is dropped.
- Remove `import pytz` when the file no longer uses it.
- Behaviour stays the same, daylight saving time included.
