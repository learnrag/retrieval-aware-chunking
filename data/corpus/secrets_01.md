# Secrets (variant 1)

## Overview
This document describes the secrets used by service cluster 1.

## Policy
Secrets are vault-backed and rotated weekly.
Related configuration keys are namespaced under `secrets.v1`.

## Operations
Operators should verify the secrets after each change window.
Escalation contacts are listed in the on-call roster for cluster 1.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
