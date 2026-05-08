# Rollback (variant 3)

## Overview
This document describes the rollback used by service cluster 3.

## Policy
Failed releases roll back to the previous revision.
Related configuration keys are namespaced under `rollback.v3`.

## Operations
Operators should verify the rollback after each change window.
Escalation contacts are listed in the on-call roster for cluster 3.

## Notes
Do not confuse this policy with legacy settings from cluster 2.
