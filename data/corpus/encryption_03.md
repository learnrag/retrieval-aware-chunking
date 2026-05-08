# Encryption (variant 3)

## Overview
This document describes the encryption used by service cluster 3.

## Policy
Data at rest uses AES-256 encryption.
Related configuration keys are namespaced under `encryption.v3`.

## Operations
Operators should verify the encryption after each change window.
Escalation contacts are listed in the on-call roster for cluster 3.

## Notes
Do not confuse this policy with legacy settings from cluster 2.
