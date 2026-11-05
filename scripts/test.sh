#!/bin/sh
# The whole test suite, run twice: with the machine's clock in UTC and in Asia/Singapore.
# IncidentDesk never depends on the machine's time zone (#24), so both runs must pass.
set -e
TZ=UTC pytest -q "$@"
TZ=Asia/Singapore pytest -q "$@"
