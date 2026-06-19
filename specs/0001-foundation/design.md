# Design — Foundation

## Shape

Three layers. A scenario library, a sealed runtime, and an unsealed
baseline for comparison.

```
scenarios/v0_10x5.json
       |
       v
+-----------------------+         +------------------------+
|  sealed runtime (MPC) |         |  unsealed baseline     |
|  produces ranking +   |         |  simulates Coupa-style |
|  receipts only        |         |  agent behavior        |
+-----------+-----------+         +-----------+------------+
            |                                 |
            +----------------+----------------+
                             v
                  surplus-delta analyzer
                             |
                             v
              reports/surplus_delta.md  (in paper appendix)
```

## Why the unsealed baseline matters

The paper's load-bearing claim is that the sealed runtime *recovers
surplus* compared to the unsealed status quo. That requires a
faithful simulation of what bid-comparison agents actually do today.
The baseline does not need to be perfect — it needs to be plausibly
disclosable. A defensible mid-point of published Coupa / Pactum
behavior is enough.

## Runtime sketch

The v0 runtime uses additive-secret-sharing plus PSI for the lot-
assignment join. It is single-buyer-side (the buyer's agent and an
audit verifier act as the two MPC parties; suppliers submit
ciphertexts).

This is deliberately the simplest defensible construction. The paper
explicitly names the threat model the v0 runtime addresses
(honest-but-curious buyer, malicious-but-non-colluding audit
verifier) and the threat model it does *not* (collusion between
buyer and audit verifier).

## Scenario shape

```json
{
  "scenario_id": "v0_10x5",
  "suppliers": [
    {"id": "S01", "capacity": {"L1": 1000, "L2": 0, "L3": 500, ...}},
    ...
  ],
  "lots": [
    {"id": "L1", "demand": 800, "scoring_weights":
      {"price": 0.7, "lead_time_days": 0.2, "esg_score": 0.1}},
    ...
  ],
  "reserve_prices": {"L1": 12.50, ...},
  "auction_rule": "first-price-sealed"
}
```

## Surplus-delta sketch

For each runtime, the analyzer computes:

- Buyer surplus = sum over lots of (max_willingness_to_pay -
  cleared_price) under that runtime's assignment.
- Supplier surplus = sum over winning suppliers of
  (cleared_price - reported_cost) where reported cost is the *true*
  cost from the scenario, not the strategically-shaded bid.

Delta = sealed total surplus − unsealed total surplus, broken out
buyer-side vs supplier-side, plus a Gini-style fairness measure.

## Dependencies

- `pyca/cryptography` for primitives in v0 (no novel crypto).
- `numpy` for scoring linear combinations.
- `pydantic` for typed scenario / receipt schemas.
- `jsonschema` for validation.
- LaTeX for the paper (Overleaf or local).

## What is deliberately NOT in v0

- Real-world Coupa / Zip / Ariba integration.
- Throughput optimization. v0 runs in seconds on the 10x5 benchmark
  and that is enough.
- Multi-buyer-side (combinatorial cross-buyer) auctions. The
  multi-hyperscaler version lives in `power-ppa-forge`.
- Production cryptography. v0 explicitly names the deployment
  threat model gap in the paper.
