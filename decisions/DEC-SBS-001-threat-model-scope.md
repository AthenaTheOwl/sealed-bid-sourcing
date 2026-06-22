# DEC-SBS-001 - Threat Model Scope

Status: accepted

## Decision

The v0.1 sealed runtime is scoped to an honest-but-curious buyer and a
non-colluding audit verifier.

## Rationale

This scope is enough to state the bounded leakage claim for the benchmark
receipt. It keeps the reference implementation inspectable while the paper
draft records the assumptions that production cryptography would need to
replace.

## Consequences

The leakage file must continue to reject losing bid values as allowed leakage.
Collusion resistance and production side-channel analysis remain future work.
