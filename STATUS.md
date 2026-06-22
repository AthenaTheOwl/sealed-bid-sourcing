# Status

## Current state

- v0.1 data-report repo is present.
- The canonical benchmark is `scenarios/v0_10x5.json`.
- The CLI validates scenarios, emits sealed and unsealed receipts, and writes a
  surplus delta report.
- The checked-in report is `reports/surplus_delta.md`.
- The leakage gate is `scripts/validate_leakage_bound.py`.

## Known limits

- The sealed runtime is reference-grade and does not implement production MPC.
- The unsealed baseline uses fixed defensive markup values from the scenario.
- The paper is a skeleton and cites the primitive family, not a full proof.
- The benchmark has one canonical 10x5 case and no generated scenario suite.

## Next feature queue

- Replace the reference sealed scorer with additive-secret-sharing and PSI
  primitives behind the same receipt schema.
- Add receipt validation against the JSON Schema when `jsonschema` is present.
- Expand the paper with the full threat model and proof sketch.
- Add a larger scenario fixture after the 10x5 benchmark stays stable.

- Resolve factory defect: implementation produced no file changes relative to base; refusing to mark a no-op as done
- Resolve factory defect: claude_code review requested patch; inspect defect log
- Resolve factory defect: missing PRODUCT_BRIEF.md,SYSTEM_MAP.md
- Resolve factory defect: missing reports/*.jsonl
- Resolve factory defect: PRODUCT_BRIEF.md is required for active repos
- Resolve factory defect: SYSTEM_MAP.md is required for active repos
- Resolve factory defect: expected file 'PRODUCT_BRIEF.md' is missing
- Resolve factory defect: expected file 'SYSTEM_MAP.md' is missing
- Resolve factory defect: expected file 'sealed_bid_sourcing/cli.py' is missing
- Resolve factory defect: expected glob 'reports/*.jsonl' matched no files
- Resolve factory defect: module 'cli' declares source 'sealed_bid_sourcing/cli.py', but it is missing
- Resolve factory defect: module 'model' declares source 'sealed_bid_sourcing/model.py', but it is missing
- Resolve factory defect: module 'report' declares source 'sealed_bid_sourcing/scoring.py', but it is missing
- Resolve factory defect: claude_code review requested patch; inspect defect log
