# Surplus Delta Report

Scenario: `v0_10x5`
Sealed receipt: `v0_10x5-sealed-v0.1.0`
Unsealed receipt: `v0_10x5-unsealed-v0.1.0`

## Headline

- Buyer surplus delta: `2259.00`
- Supplier surplus delta: `-1619.00`
- Total surplus delta: `640.00`
- Markup assumption: the unsealed baseline inflates each bid by its supplier's `defensive_markup_pct` (0.03 to 0.20 in this scenario) before scoring.
- Zero-markup control buyer surplus delta: `0.00` (see below).
- Unassigned lots: sealed none; unsealed none. An unassigned lot adds 0 buyer surplus, so a lot only one runtime leaves unassigned counts toward the delta; that is infeasibility, not a saving.

## Zero-markup Control

Same scenario with every supplier's `defensive_markup_pct` set to 0, both runtimes re-run.

- Buyer surplus delta: `0.00`
- Supplier surplus delta: `0.00`
- Total surplus delta: `0.00`

With no markup the two runtimes clear every lot the same way, so the headline delta comes entirely from the assumed markups. It is a model result conditional on those values and does not measure how real suppliers respond to disclosure.

## Runtime Totals

| Runtime | Buyer surplus | Supplier surplus | Total surplus |
|---|---:|---:|---:|
| sealed | 13430.00 | 5900.00 | 19330.00 |
| unsealed | 11171.00 | 7519.00 | 18690.00 |

## Assignment Comparison

| Lot | Sealed winner | Sealed price | Unsealed winner | Unsealed price | Total delta |
|---|---|---:|---|---:|---:|
| L1 | S07 | 11.7 | S08 | 12.57 | 400.00 |
| L2 | S08 | 18.8 | S08 | 19.36 | 0.00 |
| L3 | S08 | 23.9 | S02 | 24.13 | -180.00 |
| L4 | S07 | 9.5 | S02 | 10.61 | 420.00 |
| L5 | S08 | 30.8 | S08 | 31.72 | 0.00 |

The sealed run keeps losing bid values out of the buyer-side receipt.
Supplier and total surplus come from each run's internal audit file; neither receipt carries true costs.
The unsealed baseline applies the scenario's defensive markups before scoring.
