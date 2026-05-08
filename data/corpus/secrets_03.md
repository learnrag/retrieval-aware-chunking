# Secrets (variant 3)

## Overview
This document describes the secrets used by service cluster 3.

## Policy
Secrets are vault-backed and rotated weekly.
Related configuration keys are namespaced under `secrets.v3`.

## Operations
Operators should verify the secrets after each change window.
Escalation contacts are listed in the on-call roster for cluster 3.

## Notes
Do not confuse this policy with legacy settings from cluster 2.
