# AGENTS.md - sealed-bid-sourcing

Operating contract for AI agents working in this repo. Conventions match the
rest of the AthenaTheOwl portfolio.

## What this repo is

A benchmark plus reference implementation for MPC-backed sealed-bid reverse
auctions in procurement. The runtime is the artifact, the paper is the receipt,
and the surplus-recovery delta is the proof surface.

This is a research-shape repo with cryptography in it. Caution required.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `scenario-author` | Authors typed procurement scenarios. |
| `runtime-engineer` | Builds the MPC/PSI reference runtime. |
| `leakage-prover` | Writes bounded-leakage proof material under `paper/`. |
| `surplus-analyst` | Runs sealed vs unsealed baseline and emits the delta. |
| `paper-writer` | Maintains `paper/sealed-bid-sourcing.tex`. |

## Voice constraints

- The paper draft is the load-bearing surface. Read it through the voice lint
  before each commit.
- No marketing words. The mechanism design speaks for itself.
- No antithetical-reversal phrasing.
- Cryptographic claims must cite. If a leakage bound shows up in prose, the
  paper bibliography must have the underlying construction.

## Gates

```bash
python -m pytest
python scripts/voice_lint.py paper/ README.md
python scripts/validate_schemas.py schemas/ scenarios/ runs/
python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml --runtime sealed
```

The `validate_leakage_bound.py` gate is the load-bearing one. A runtime change
that alters the leakage profile must update the bound file or the build fails.

## Out of scope

- Production-ready MPC runtime. v0.1 is reference-implementation grade,
  optimized for correctness and auditability, not throughput.
- Coupa, Zip, or Ariba native plugins. The runtime sits next to them. Integration
  is a separate later artifact.
- Cryptocurrency or on-chain settlement. The audit trail is the receipt;
  settlement is out-of-band.
- Forward-auction variants. Reverse only in v0.1.
