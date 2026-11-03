# Priority rules

Every incident gets a priority from P1 (most urgent) to P4 when it is opened.

1. The severity sets the starting priority: critical P1, major P2, minor P3, cosmetic P4.
2. Customer-facing services are raised one level, at any hour of the day. P1 stays P1.
3. An incident opened inside a maintenance window of its service is lowered one level. P4 stays P4.

Business hours (09:00-18:00, Monday to Friday, in the service time zone) never change the priority. They only decide
who responds first: the service team during business hours, the on-call engineer outside them (`docs/routing.md`).

Examples, for a major incident on `login-service` (customer-facing):

| Opened (service time) | Priority |
|---|---|
| Tuesday 14:00 | P1 |
| Tuesday 23:30 | P1 |
| Saturday 10:00 | P1 |
