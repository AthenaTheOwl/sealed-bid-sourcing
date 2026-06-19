# Requirements — Foundation

Brand prefix: SBS (sealed-bid-sourcing).

## Scenario requirements

- **R-SBS-001** — The repo SHALL define a typed scenario schema
  `schemas/scenario.schema.json` covering: suppliers (n), lots (m),
  per-lot scoring weights, capacity constraints per supplier,
  optional reserve prices, optional Vickrey rule selection.
- **R-SBS-002** — A v0 scenario SHALL support multi-attribute scoring
  (price plus at least one non-price attribute such as lead-time or
  ESG score), matching the procurement shape supplier-side care
  about, not academic single-attribute toy cases.
- **R-SBS-003** — The repo SHALL ship one canonical benchmark
  instance `scenarios/v0_10x5.json` (10 suppliers, 5 lots) used as
  the reference workload throughout the paper.

## Runtime requirements

- **R-SBS-004** — The runtime SHALL accept committed ciphertext bids
  from each supplier and produce a ranking without opening losing
  bids.
- **R-SBS-005** — The runtime SHALL produce a typed run-receipt
  including: scenario hash, supplier commitment hashes, winning
  supplier and lot assignment, opened winning-bid values, runtime
  version.
- **R-SBS-006** — The runtime SHALL be implementable with off-the-
  shelf PSI / additive-secret-sharing primitives; no novel
  cryptography in v0.

## Proof requirements

- **R-SBS-007** — The repo SHALL maintain
  `paper/leakage_bounds.yaml` naming the bounded information the
  runtime leaks to the buyer (e.g., "ranking only, no losing-bid
  values").
- **R-SBS-008** — Any runtime change SHALL update
  `paper/leakage_bounds.yaml` in the same PR or fail the gate.

## Surplus-delta requirements

- **R-SBS-009** — The repo SHALL define an unsealed-baseline runtime
  that simulates a Coupa-style bid-comparison agent's behavior
  against the same scenario.
- **R-SBS-010** — The surplus-delta tool SHALL compute the
  buyer-side and supplier-side surplus under both runtimes and emit
  the delta as a typed report.

## Voice and gate requirements

- **R-SBS-011** — The paper draft and README SHALL pass voice_lint.
- **R-SBS-012** — All cryptographic claims in the paper SHALL be
  backed by a bibliographic citation in `paper/refs.bib`.
