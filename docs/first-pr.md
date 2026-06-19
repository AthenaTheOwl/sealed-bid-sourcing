# First PR (after scaffold)

The literal first PR after this v0 scaffold is PR 0002: scenario
schema, the canonical 10x5 benchmark instance, and the paper
skeleton.

## Scope

One reviewable PR. No runtime code yet. The shape of the inputs and
the shape of the paper come first so the runtime work in PR 0003 has
a typed target.

## Files added

```
schemas/scenario.schema.json
schemas/receipt.schema.json
scenarios/v0_10x5.json
paper/sealed-bid-sourcing.tex
paper/refs.bib
paper/leakage_bounds.yaml
src/sealed_bid_sourcing/__init__.py
src/sealed_bid_sourcing/__main__.py
src/sealed_bid_sourcing/cli.py
scripts/voice_lint.py
scripts/validate_schemas.py
scripts/validate_leakage_bound.py
tests/test_scenario_validates.py
pyproject.toml
```

## Files changed

```
README.md         # "How to run" gets the validate command
AGENTS.md         # uncomment the gate block (now real)
```

## Why this scope

The scenario schema is the load-bearing decision. Every later PR
writes into it or reads from it: the sealed runtime, the unsealed
baseline, the surplus-delta analyzer, the paper results table. Get
the typed shape right first.

The benchmark instance `v0_10x5.json` is hand-authored, not random.
It includes one supplier with zero capacity in one lot (tests the
capacity-constraint enforcement), one lot with a binding reserve
price (tests reserve handling), and a mix of price-dominant and
attribute-dominant scoring weights (tests multi-attribute scoring).

The paper skeleton sets section structure plus the abstract. The
bibliography pins citations for the underlying primitives now so
later PRs that touch the runtime never quietly cite something the
implementation does not actually use.

## Verification

```bash
python -m pip install -e .[dev]
python -m pytest
python scripts/voice_lint.py README.md AGENTS.md paper/
python scripts/validate_schemas.py scenarios/v0_10x5.json
python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
cd paper && pdflatex -interaction=nonstopmode sealed-bid-sourcing.tex
```

The last command should produce `paper/sealed-bid-sourcing.pdf` with
the abstract rendered and a clean log.

## Out of scope (deferred to PR 0003)

- The sealed runtime.
- The unsealed baseline.
- Receipt generation.
- The surplus-delta analyzer.

## Decision record

PR 0002 lands `decisions/DEC-SBS-000-benchmark-shape.md` recording
why the v0 benchmark is 10x5 (small enough to reason about by hand,
large enough to expose capacity-binding and reserve-price corners)
and what would have to be true to ship a v1 with a larger benchmark.
