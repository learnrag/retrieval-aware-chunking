# Timeouts (variant 1)

## Overview
This document describes the timeouts used by service cluster 1.

## Policy
Upstream timeouts are set to 30 seconds.
Related configuration keys are namespaced under `timeouts.v1`.

## Operations
Operators should verify the timeouts after each change window.
Escalation contacts are listed in the on-call roster for cluster 1.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
