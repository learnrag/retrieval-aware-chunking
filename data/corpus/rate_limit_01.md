# Rate Limits (variant 1)

## Overview
This document describes the rate limits used by service cluster 1.

## Policy
API clients are limited to 100 requests per minute.
Related configuration keys are namespaced under `rate_limit.v1`.

## Operations
Operators should verify the rate limits after each change window.
Escalation contacts are listed in the on-call roster for cluster 1.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
