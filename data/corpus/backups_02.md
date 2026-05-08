# Backup Policy (variant 2)

## Overview
This document describes the backup policy used by service cluster 2.

## Policy
Backups are performed every 6 hours.
Related configuration keys are namespaced under `backups.v2`.

## Operations
Operators should verify the backup policy after each change window.
Escalation contacts are listed in the on-call roster for cluster 2.

## Notes
Do not confuse this policy with legacy settings from cluster 1.
