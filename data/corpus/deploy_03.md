# Deployments (variant 3)

## Overview
This document describes the deployments used by service cluster 3.

## Policy
Production releases use blue-green deployments.
Related configuration keys are namespaced under `deploy.v3`.

## Operations
Operators should verify the deployments after each change window.
Escalation contacts are listed in the on-call roster for cluster 3.

## Notes
Do not confuse this policy with legacy settings from cluster 2.
