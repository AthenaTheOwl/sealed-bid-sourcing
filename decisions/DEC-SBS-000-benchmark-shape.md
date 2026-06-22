# DEC-SBS-000 - Benchmark Shape

Status: accepted

## Decision

The v0 benchmark is fixed at ten suppliers and five lots.

## Rationale

The benchmark is small enough to audit by hand and large enough to cover the
minimum behavior needed by the runtime: zero capacity on a supplier-lot pair,
reserve-price filtering, price-dominant scoring, and attribute-dominant
scoring.

## Consequences

Future benchmark expansion must keep the 10x5 case as a regression fixture.
Larger scenarios can be added after the sealed and unsealed runtime behavior is
stable against this fixture.
