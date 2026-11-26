# Notes for #12: night incidents

Collected by the delivery team. Quotes are the person's own words. A `?` marks something nobody has checked yet.

## Mei Tanaka, SRE, after her on-call week

- "On Tuesday a major incident on login-service was opened at 23:30. It came in as P2."
- "The same incident opened at 14:00 is P1."
- "login-service is customer-facing, so it should be raised one level. At night it was not."
- "Saturday 10:00 looked the same to me: P2 instead of P1." ?
- "A critical incident at night must never be lowered. Never."
- "When a lot of customers are hit, a night incident should be P1 whatever its severity." Nobody has said how many customers that means.
- "A P1 must page the on-call engineer at any hour. That part works."

## Tomás Silva, Tech Lead, in the team chat

- "Business hours decide who answers first: the service team by day, the on-call engineer at night. Keep it that way."
- "I think the night rule was put in on purpose, so the on-call engineer is not woken up for every customer-facing incident."
- "Whatever we change, the routing tests must pass unchanged."
- "One rule per line in docs/priority-rules.md. If the code and the document disagree, the document wins."

## Not asked yet

- Product: does any customer contract promise a different priority at night? ?
