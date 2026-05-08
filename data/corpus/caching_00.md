# Caching (variant 0)

## Overview
This document describes the caching used by service cluster 0.

## Policy
Responses are cached with a 5 minute TTL.
Related configuration keys are namespaced under `caching.v0`.

## Operations
Operators should verify the caching after each change window.
Escalation contacts are listed in the on-call roster for cluster 0.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
