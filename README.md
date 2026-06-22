# Sealed-Bid Sourcing Layer

Sealed Bid Sourcing is a reference benchmark for sealed-bid reverse sourcing.
It compares a sealed receipt-producing runtime with an unsealed baseline on the
same multi-attribute procurement scenario.

## What this is

The repo is a v0.1 data-report artifact:

- `scenarios/v0_10x5.json` defines ten suppliers and five lots.
- `schemas/` defines scenario and receipt JSON surfaces.
- `src/sealed_bid_sourcing/` provides the CLI.
- `runs/` contains checked-in sealed and unsealed receipts.
- `reports/surplus_delta.md` contains the surplus comparison.
- `paper/` contains the draft paper surface and leakage bound.

The sealed runtime opens winning bid values in the receipt. Losing bid values
stay out of the buyer-side output. The unsealed baseline applies supplier
defensive markups before reserve filtering and scoring.

## Current state

v0.1 is a reference implementation and report fixture. It is built for
correctness, auditability, and repeatable review on the canonical benchmark.
It is not production MPC.

## How to run

```bash
python -m uv run pytest
python -m uv run python scripts/voice_lint.py paper/ README.md
python -m uv run python scripts/validate_schemas.py schemas/ scenarios/ runs/
python -m uv run python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml --runtime sealed
python -m uv run python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
```

To regenerate the checked-in run artifacts:

```bash
python -m uv run python -m sealed_bid_sourcing run \
  --scenario scenarios/v0_10x5.json \
  --runtime sealed \
  --out runs/sealed_v0/

python -m uv run python -m sealed_bid_sourcing run \
  --scenario scenarios/v0_10x5.json \
  --runtime unsealed \
  --out runs/unsealed_v0/

python -m uv run python -m sealed_bid_sourcing surplus-delta \
  --sealed runs/sealed_v0/receipt.json \
  --unsealed runs/unsealed_v0/receipt.json \
  --out reports/surplus_delta.md
```

Without uv, the package also runs from a local editable install:

```bash
python -m pytest
python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
```

## Layout

```text
sealed-bid-sourcing/
  docs/
    product-brief.md
    system-map.md
  specs/
    0001-foundation/
    0002-design/
  schemas/
    scenario.schema.json
    receipt.schema.json
  scenarios/
    v0_10x5.json
  src/sealed_bid_sourcing/
  scripts/
  tests/
  runs/
  reports/
  paper/
  decisions/
  STATUS.md
```

## License

MIT. See [LICENSE](LICENSE).
