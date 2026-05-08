# Deployments (variant 1)

## Overview
This document describes the deployments used by service cluster 1.

## Policy
Production releases use blue-green deployments.
Related configuration keys are namespaced under `deploy.v1`.

## Operations
Operators should verify the deployments after each change window.
Escalation contacts are listed in the on-call roster for cluster 1.

## Notes
Do not confuse this policy with legacy settings from cluster 0.
