# Queues (variant 1)

## Overview
This document describes the queues used by service cluster 1.

## Policy
Workers consume messages with at-least-once delivery.
Related configuration keys are namespaced under `queue.v1`.

## Operations
Operators should verify the queues after each change window.
Escalation contacts are listed in the on-call roster for cluster 1.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
