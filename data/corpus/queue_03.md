# Queues (variant 3)

## Overview
This document describes the queues used by service cluster 3.

## Policy
Workers consume messages with at-least-once delivery.
Related configuration keys are namespaced under `queue.v3`.

## Operations
Operators should verify the queues after each change window.
Escalation contacts are listed in the on-call roster for cluster 3.

## Notes
Do not confuse this policy with legacy settings from cluster 2.
