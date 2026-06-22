# Design - v0.1 Data Report

## Shape

The v0.1 implementation is intentionally small:

1. Load `scenarios/v0_10x5.json`.
2. Validate supplier, lot, capacity, scoring, reserve, and bid fields.
3. Score each lot under the selected runtime.
4. Emit a receipt that matches `schemas/receipt.schema.json`.
5. Compare sealed and unsealed receipts into `reports/surplus_delta.md`.

## Scoring

Each lot normalizes eligible bids over the candidate set for that lot. Price and
lead time are lower-is-better metrics. ESG and quality are higher-is-better
metrics. The weighted score chooses the winner, with price and supplier id as
stable tie breakers.

## Sealed Runtime

The sealed runtime uses the submitted unit price for scoring. The receipt
includes supplier commitment hashes for all suppliers and opened bid details for
winning assignments only.

## Unsealed Baseline

The unsealed baseline applies each supplier's `defensive_markup_pct` before
reserve filtering and scoring. This models a disclosed-bid environment where
suppliers shade prices.

## Report

The report compares buyer, supplier, and total surplus. Buyer surplus is
`(max_willingness_to_pay - cleared_unit_price) * demand`. Supplier surplus is
`(cleared_unit_price - true_unit_cost) * demand`.
