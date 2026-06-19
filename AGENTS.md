# AGENTS.md — sealed-bid-sourcing

Operating contract for AI agents working in this repo. Conventions
match the rest of the AthenaTheOwl portfolio.

## What this repo is

A benchmark plus reference implementation for MPC-backed sealed-bid
reverse auctions in procurement. The runtime is the artifact, the
paper is the receipt, the surplus-recovery delta is the proof.

This is a research-shape repo with cryptography in it. Caution
required.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `scenario-author` | Authors typed procurement scenarios (suppliers, lots, scoring weights) |
| `runtime-engineer` | Builds the MPC/PSI reference runtime; correctness over speed in v0 |
| `leakage-prover` | Writes the bounded-leakage proof for each runtime; checked into paper/ |
| `surplus-analyst` | Runs sealed vs unsealed baseline; emits the recovery delta |
| `paper-writer` | Lands paper/sealed-bid-sourcing.tex |

These roles exist in spec ledger; not all are implemented in v0.

## Voice constraints

- The paper draft is the load-bearing surface. Read it through the
  voice_lint before each commit.
- No marketing words. The mechanism design speaks for itself.
- No antithetical-reversal phrasing.
- Cryptographic claims must cite. If a leakage bound shows up in
  prose, the paper bibliography must have the underlying construction.

## Gates (will land in spec 0002)

```bash
python -m pytest
python scripts/voice_lint.py paper/ README.md
python scripts/validate_schemas.py scenarios/
python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml
```

The `validate_leakage_bound.py` gate is the load-bearing one. A
runtime change that alters the leakage profile must update the bound
file or the build fails.

## Out of scope

- Production-ready MPC runtime. v0 is reference-implementation grade,
  optimized for correctness and auditability, not throughput.
- Coupa / Zip / Ariba native plugins. The runtime sits next to them,
  not inside them. Integration is a separate later artifact.
- Cryptocurrency / on-chain settlement. The audit trail is the
  receipt; settlement is out-of-band.
- Forward-auction (English / Dutch) variants. Reverse only in v0.
