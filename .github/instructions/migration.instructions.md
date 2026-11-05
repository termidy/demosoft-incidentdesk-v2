---
applyTo: "incidentdesk/**/*.py"
---

# Moving from pytz to zoneinfo (#24)

- In every Python file you change, replace pytz with zoneinfo: `ZoneInfo("America/Chicago")` instead of `pytz.timezone("America/Chicago")`, `timezone.utc` instead of `pytz.utc`.
- `tz.localize(dt)` becomes `dt.replace(tzinfo=tz)`, and `tz.normalize(...)` is dropped.
- Remove `import pytz` when the file no longer uses it.
- Move the module's tests in `tests/unit/` in the same change.
- Behaviour stays the same, daylight saving time included.