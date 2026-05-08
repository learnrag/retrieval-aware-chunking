# Caching (variant 4)

## Overview
This document describes the caching used by service cluster 4.

## Policy
Responses are cached with a 5 minute TTL.
Related configuration keys are namespaced under `caching.v4`.

## Operations
Operators should verify the caching after each change window.
Escalation contacts are listed in the on-call roster for cluster 4.

## Notes
Do not confuse this policy with legacy settings from cluster 3.
