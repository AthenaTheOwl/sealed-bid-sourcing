# System Map

```text
scenarios/v0_10x5.json
        |
        v
src/sealed_bid_sourcing/cli.py
        |
        +-- validate ----------------------+
        |                                  |
        +-- run --runtime sealed           v
        |                         schemas/scenario.schema.json
        |                         schemas/receipt.schema.json
        |
        +-- run --runtime unsealed
        |
        v
runs/sealed_v0/receipt.json
runs/unsealed_v0/receipt.json
        |
        v
reports/surplus_delta.md
        |
        v
paper/sealed-bid-sourcing.tex
paper/leakage_bounds.yaml
```

## Runtime Boundary

The v0.1 sealed runtime is a reference implementation. It represents the audit
surface for a sealed run: scenario hash, supplier commitments, winner ids,
opened winning bids, and surplus totals. It does not implement production MPC.

## Gate Boundary

The repository gates check three things:

- Scenario and receipt JSON are well formed for the benchmark surface.
- The leakage file names the fields exposed by the sealed runtime.
- The paper and README avoid banned voice patterns.
