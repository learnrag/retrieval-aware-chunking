# Logging (variant 2)

## Overview
This document describes the logging used by service cluster 2.

## Policy
Application logs are emitted as JSON lines.
Related configuration keys are namespaced under `logging.v2`.

## Operations
Operators should verify the logging after each change window.
Escalation contacts are listed in the on-call roster for cluster 2.

## Notes
Do not confuse this policy with legacy settings from cluster 1.
