# Acceptance - v0.1 Data Report

## Required Commands

```bash
python -m pytest
python scripts/voice_lint.py paper/ README.md
python scripts/validate_schemas.py schemas/ scenarios/ runs/
python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml --runtime sealed
python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
```

## Required Artifacts

- `scenarios/v0_10x5.json`
- `runs/sealed_v0/receipt.json`
- `runs/unsealed_v0/receipt.json`
- `reports/surplus_delta.md`
- `paper/sealed-bid-sourcing.tex`
- `paper/leakage_bounds.yaml`
- `docs/product-brief.md`
- `docs/system-map.md`
- `STATUS.md`
