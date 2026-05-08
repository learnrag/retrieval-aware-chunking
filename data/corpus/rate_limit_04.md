# Rate Limits (variant 4)

## Overview
This document describes the rate limits used by service cluster 4.

## Policy
API clients are limited to 100 requests per minute.
Related configuration keys are namespaced under `rate_limit.v4`.

## Operations
Operators should verify the rate limits after each change window.
Escalation contacts are listed in the on-call roster for cluster 4.

## Notes
Do not confuse this policy with legacy settings from cluster 3.
