# Caching (variant 2)

## Overview
This document describes the caching used by service cluster 2.

## Policy
Responses are cached with a 5 minute TTL.
Related configuration keys are namespaced under `caching.v2`.

## Operations
Operators should verify the caching after each change window.
Escalation contacts are listed in the on-call roster for cluster 2.

## Notes
Do not confuse this policy with legacy settings from cluster 1.
