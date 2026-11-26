# ADR 0001: Business hours do not change priority

## Context

A customer-facing incident opened at night received a lower priority than the same incident opened during the day,
although the documented rule required a one-level increase at any hour. ([Issue #12](https://github.com/termidy/demosoft-incidentdesk-v2/issues/12))

## Decision

Apply the customer-facing priority increase regardless of business hours; keep the priority bounds and apply the
maintenance adjustment after the increase. ([PR #55](https://github.com/termidy/demosoft-incidentdesk-v2/pull/55),
[clamping commit](https://github.com/termidy/demosoft-incidentdesk-v2/commit/8b4d91ad903dd0a112802ed04ceb4e102ba6f5e8))

## Consequences

- A major customer-facing incident is P1 on Tuesday afternoon, Tuesday night, and Saturday morning. ([PR #55](https://github.com/termidy/demosoft-incidentdesk-v2/pull/55))
- A critical customer-facing incident in maintenance is lowered from P1 to P2. ([Clamping commit](https://github.com/termidy/demosoft-incidentdesk-v2/commit/8b4d91ad903dd0a112802ed04ceb4e102ba6f5e8))
- Routing remains separate: business hours continue to determine responder selection. ([PR #55](https://github.com/termidy/demosoft-incidentdesk-v2/pull/55))
- Previously stored incidents were outside the scope of the fix. ([Issue #12](https://github.com/termidy/demosoft-incidentdesk-v2/issues/12))

Gap: The cited issue and fix do not record a broader business rationale or alternatives considered for the rule.
