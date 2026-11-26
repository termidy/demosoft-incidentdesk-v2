# Night priority

## Business intent

- Raise customer-facing incidents one priority level at any hour, so a comparable incident is not treated as less urgent just because it opened at night. (notes L7-L9)
- Keep the response assignment based on business hours: the service team by day and the on-call engineer at night. (notes L17)
- A P1 pages the on-call engineer at any hour. (notes L13)

## IT intent

- Align the priority calculation with the documented all-hours customer-facing increase, including Saturday; the current code limits the increase to business hours, and the priority document takes precedence when they disagree. (notes L9, L20; Saturday: the examples in docs/priority-rules.md, because L10 is not checked)
- Keep routing behavior and its tests unchanged while adjusting priority behavior. (notes L17, L19)
- Do not add a night-specific downgrade for critical incidents; maintenance-window downgrades may still apply, per interview clarification. (notes L11)

## Never

- Never lower a critical incident because it opened at night. (notes L11)
- Never change routing as part of this priority change. (notes L17, L19)

## Open questions

- Tomás: Is the concern about waking the on-call engineer for every customer-facing incident acceptable given that a night-time P1 pages on-call? (notes L13, L18)
- What number of affected customers qualifies as “a lot” and makes a night incident P1? (notes L12)
- Does any customer contract promise a different priority at night? (notes L24)
