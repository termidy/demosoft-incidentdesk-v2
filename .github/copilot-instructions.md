# Instructions for Copilot in incidentdesk

- Every change that users can notice adds one line to CHANGELOG.md
  under "## Unreleased", in plain words for on-call engineers.

- Run the tests with `scripts/test.sh`, not plain `pytest`: it runs the suite twice,
  with the machine's clock in UTC and in Asia/Singapore (#24).
