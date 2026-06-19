# Tasks — Foundation

## PR 0002 — scenario schema, benchmark instance, paper skeleton

- [ ] Write `schemas/scenario.schema.json` matching R-SBS-001 and
      R-SBS-002.
- [ ] Author `scenarios/v0_10x5.json` matching R-SBS-003.
- [ ] Add `paper/sealed-bid-sourcing.tex` skeleton with section
      headings and the abstract.
- [ ] Add `paper/refs.bib` seeded with the ScienceDirect Jan 2026
      PSI paper plus 4 underlying primitives.
- [ ] Add `paper/leakage_bounds.yaml` with the v0 threat-model
      placeholder.
- [ ] Add `scripts/voice_lint.py` (copy template).
- [ ] Add `scripts/validate_schemas.py` and
      `scripts/validate_leakage_bound.py`.
- [ ] Add `pyproject.toml`.

## PR 0003 — runtime reference implementation

- [ ] Implement `src/sealed_bid_sourcing/runtime/sealed.py` using
      additive-secret-sharing + PSI primitives from
      `pyca/cryptography`.
- [ ] Implement `src/sealed_bid_sourcing/runtime/unsealed.py` as the
      Coupa-style baseline.
- [ ] Implement `src/sealed_bid_sourcing/receipt.py` for
      run-receipt emission (R-SBS-005).
- [ ] Write `tests/test_sealed_runtime.py` against `v0_10x5.json`.
- [ ] Verify run-receipts validate against schema.

## PR 0004 — surplus-delta analysis and paper draft v0

- [ ] Implement `src/sealed_bid_sourcing/analysis/surplus_delta.py`.
- [ ] Run both runtimes on `v0_10x5.json`; emit
      `reports/surplus_delta.md`.
- [ ] Fill paper sections: intro, threat model, runtime sketch,
      benchmark, results table, limitations.
- [ ] Add `decisions/DEC-SBS-001-threat-model-scope.md`.
- [ ] Add `decisions/DEC-SBS-002-pyca-as-v0-crypto.md`.
- [ ] Tag `v0.1` once voice_lint plus validate_leakage_bound pass.
