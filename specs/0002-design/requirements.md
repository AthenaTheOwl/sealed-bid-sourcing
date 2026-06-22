# Requirements - Design Ledger

Brand prefix: SBS.

## Data and Report Requirements

- **R-SBS-013** - The repo SHALL expose a runnable Python CLI with
  `validate`, `run`, and `surplus-delta` subcommands.
- **R-SBS-014** - The repo SHALL check in one sealed receipt, one unsealed
  receipt, and one surplus delta report for the canonical benchmark.
- **R-SBS-015** - `STATUS.md` SHALL include the exact H2 sections
  `Current state`, `Known limits`, and `Next feature queue`.
- **R-SBS-016** - Python development dependencies SHALL live under
  `[dependency-groups]` and `[tool.uv] package = true` SHALL be set.

## Runtime Requirements

- **R-SBS-017** - The sealed v0.1 runtime SHALL open only winning bid values in
  the emitted receipt.
- **R-SBS-018** - The unsealed baseline SHALL score the same bids after applying
  supplier defensive markup.
- **R-SBS-019** - The surplus report SHALL compute buyer, supplier, and total
  surplus deltas from receipt files.
