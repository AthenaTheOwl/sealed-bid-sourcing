# DEC-SBS-002 - PyCA as v0 Crypto Boundary

Status: accepted

## Decision

Production cryptographic primitives are out of scope for v0.1. A later runtime
that adds concrete primitives should use maintained Python cryptography
packages rather than novel cryptography in this repo.

## Rationale

The v0.1 artifact is a data-report benchmark. Its job is to make the scenario,
receipt, leakage, and surplus surfaces reviewable. Cryptographic hardening is a
separate implementation step.

## Consequences

Any runtime change that claims stronger privacy must update
`paper/leakage_bounds.yaml`, citations, and tests in the same change.
