# Replication (variant 3)

## Overview
This document describes the replication used by service cluster 3.

## Policy
Replicas are kept in a cross-region pair.
Related configuration keys are namespaced under `replication.v3`.

## Operations
Operators should verify the replication after each change window.
Escalation contacts are listed in the on-call roster for cluster 3.

## Notes
Do not confuse this policy with legacy settings from cluster 2.
