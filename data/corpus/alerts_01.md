# Alerting (variant 1)

## Overview
This document describes the alerting used by service cluster 1.

## Policy
Critical pages route to PagerDuty.
Related configuration keys are namespaced under `alerts.v1`.

## Operations
Operators should verify the alerting after each change window.
Escalation contacts are listed in the on-call roster for cluster 1.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
