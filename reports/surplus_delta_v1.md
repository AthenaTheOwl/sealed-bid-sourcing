# Surplus Delta Report

Scenario: `v1_20x10`
Sealed receipt: `v1_20x10-sealed-v0.1.0`
Unsealed receipt: `v1_20x10-unsealed-v0.1.0`

## Headline

- Buyer surplus delta: `9008.30`
- Supplier surplus delta: `-6861.30`
- Total surplus delta: `2147.00`

## Runtime Totals

| Runtime | Buyer surplus | Supplier surplus | Total surplus |
|---|---:|---:|---:|
| sealed | 54173.00 | 20454.00 | 74627.00 |
| unsealed | 45164.70 | 27315.30 | 72480.00 |

## Assignment Comparison

| Lot | Sealed winner | Sealed price | Unsealed winner | Unsealed price | Total delta |
|---|---|---:|---|---:|---:|
| L1 | S07 | 11.8 | S08 | 12.67 | 600.00 |
| L10 | S18 | 62.1 | S18 | 64.58 | 0.00 |
| L2 | S08 | 23.0 | S08 | 23.69 | 0.00 |
| L3 | S03 | 36.0 | S08 | 36.26 | -210.00 |
| L4 | S07 | 9.7 | S08 | 10.92 | 665.00 |
| L5 | S08 | 52.2 | S08 | 53.77 | 0.00 |
| L6 | S17 | 13.3 | S18 | 14.56 | 770.00 |
| L7 | S18 | 27.1 | S18 | 28.18 | 0.00 |
| L8 | S13 | 40.6 | S18 | 41.81 | -128.00 |
| L9 | S17 | 9.1 | S18 | 10.19 | 450.00 |

The sealed run keeps losing bid values out of the buyer-side receipt.
The unsealed baseline applies the scenario's defensive markups before scoring.
