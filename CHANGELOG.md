# Changelog

What changed for the people who use IncidentDesk: on-call engineers, support and the reporting team.

## Unreleased

- Customer-facing incidents are raised one priority level at any hour.

## 1.4.0

- The daily report counts incidents by the local calendar day.
- Monitoring alerts that repeat within ten minutes are marked as duplicates.
- Support emails use the customer's own time zone (`Reported-TZ`).

## 1.3.0

- Every service gets a weekly maintenance window, Sunday 02:00-04:00 service time.
- An incident opened during maintenance gets one priority level lower.
- The status page shows only customer-facing P1 and P2 incidents.

## 1.2.0

- The handoff note lists the open incidents of the rotation.
- The morning digest arrives at 08:00 in the recipient's own time zone.
- A P1 that nobody acknowledges escalates to the team lead after ten minutes.

## 1.1.0

- CSV export of incidents for the reporting team.
- `GET /incidents/{key}/timeline` with a `since` filter.

## 1.0.0

- First release: incidents, priorities, SLA tracking and postmortems.
