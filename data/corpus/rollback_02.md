# Rollback (variant 2)

## Overview
This document describes the rollback used by service cluster 2.

## Policy
Failed releases roll back to the previous revision.
Related configuration keys are namespaced under `rollback.v2`.

## Operations
Operators should verify the rollback after each change window.
Escalation contacts are listed in the on-call roster for cluster 2.

## Notes
Do not confuse this policy with legacy settings from cluster 1.
