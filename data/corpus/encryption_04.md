# Encryption (variant 4)

## Overview
This document describes the encryption used by service cluster 4.

## Policy
Data at rest uses AES-256 encryption.
Related configuration keys are namespaced under `encryption.v4`.

## Operations
Operators should verify the encryption after each change window.
Escalation contacts are listed in the on-call roster for cluster 4.

## Notes
Do not confuse this policy with legacy settings from cluster 3.
