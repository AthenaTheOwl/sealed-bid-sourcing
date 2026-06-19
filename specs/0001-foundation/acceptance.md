# Acceptance — v0 Foundation

"v0 done" means the canonical 10-supplier 5-lot benchmark runs end-
to-end under both runtimes, the surplus-delta report exists, the
paper draft compiles, and the leakage-bound file matches the runtime
in use.

## Commands a reviewer must be able to run

```bash
python -m pip install -e .[dev]

python -m sealed_bid_sourcing validate scenarios/v0_10x5.json

python -m sealed_bid_sourcing run \
  --scenario scenarios/v0_10x5.json \
  --runtime sealed \
  --out runs/sealed_v0/

python -m sealed_bid_sourcing run \
  --scenario scenarios/v0_10x5.json \
  --runtime unsealed \
  --out runs/unsealed_v0/

python -m sealed_bid_sourcing surplus-delta \
  --sealed runs/sealed_v0/receipt.json \
  --unsealed runs/unsealed_v0/receipt.json \
  --out reports/surplus_delta.md

cd paper && pdflatex sealed-bid-sourcing.tex
```

## Gates that must pass

- `python -m pytest` exits 0.
- `python scripts/voice_lint.py paper/ README.md` exits 0.
- `python scripts/validate_schemas.py scenarios/ runs/` exits 0.
- `python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml
  --runtime sealed` exits 0.

## Artifacts that must exist

- `scenarios/v0_10x5.json` — the canonical benchmark.
- `runs/sealed_v0/receipt.json` and `runs/unsealed_v0/receipt.json`
  — both runtimes' outputs on the benchmark.
- `reports/surplus_delta.md` — the headline number.
- `paper/sealed-bid-sourcing.pdf` — compiled draft.
- `paper/leakage_bounds.yaml` — matches the deployed sealed runtime.
- `decisions/DEC-SBS-001` and `DEC-SBS-002`.

## Out of scope for v0

- Production deployment integration with Coupa / Zip / Ariba.
- Performance benchmarks beyond "completes in seconds on 10x5".
- Adversarial / malicious-buyer threat model. v0 explicitly bounds
  to honest-but-curious.
- Multi-buyer combinatorial extension.

## What "done" feels like

A procurement-academic peer reads `paper/sealed-bid-sourcing.pdf`
and can re-run the benchmark with the published artifact. They get
the same surplus-delta number. They can verify the leakage bound
against the implementation by reading `leakage_bounds.yaml` and
diffing it against the runtime source. That is the bar.
