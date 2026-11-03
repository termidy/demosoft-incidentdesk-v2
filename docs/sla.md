# SLA

Each priority has two targets, measured from the moment the incident was opened.

| Priority | Response (acknowledged within) | Resolution (resolved within) |
|---|---|---|
| P1 | 15 minutes | 4 hours |
| P2 | 30 minutes | 8 hours |
| P3 | 4 hours | 3 days |
| P4 | 1 day | 10 days |

- **Response** is met when the incident is acknowledged before its response due time.
- **Resolution** is met when the incident is resolved before its resolution due time.
- Time while the incident waits on the customer (status `waiting`) does not count: the resolution due time moves later by
  the time spent waiting. The response target is never paused.
- An open incident whose due time has passed is already in breach; it does not wait to be closed.
- A breach is reported once per target.
