# Sealed-Bid Sourcing Layer

An MPC/PSI-backed sealed-bid auction runtime that plugs into existing
e-sourcing tools (Coupa, Zip, Ariba) so suppliers get a cryptographic
guarantee that their bid is only used for ranking — restoring
strategyproofness to reverse auctions that have visibly lost it.

## What this is

Coupa and Pactum shipped 20+ persona-based bid-comparison agents and
LLM-driven negotiation bots through 2024-2026. Suppliers responded by
shading bids defensively because they cannot verify what the buyer's
agent does with the disclosed price. The reverse auction is no longer
strategyproof, and supplier-side trade associations have begun telling
members to stop submitting best price.

This repo is the public benchmark and reference implementation of an
MPC-backed sealed-bid layer that sits next to (not inside) Coupa /
Zip / Ariba. Suppliers submit ciphertexts; the runtime ranks; only
the winner's bid is opened. The buyer's bid-comparison agent never
sees losing prices.

## Status

v0 scaffold. No implementation yet. Specs in `specs/0001-foundation/`
name the scenario class, the leakage-bound proof obligation, and the
first 10-supplier-5-lot benchmark. PR 0002 will extend
`procurement-negotiation-lab` with the sealed-bid scenario class and
land a paper draft skeleton.

## How to run

Placeholder. Will land in spec 0002. The intended invocation:

```bash
python -m sealed_bid_sourcing scenario create \
  --suppliers 10 --lots 5 --out scenarios/v0.json
python -m sealed_bid_sourcing run \
  --scenario scenarios/v0.json \
  --runtime mpc-reference \
  --out runs/v0/
python -m sealed_bid_sourcing surplus-delta \
  --sealed runs/v0/sealed.json \
  --unsealed runs/v0/unsealed.json \
  --out reports/surplus_delta.md
```

## Layout

```
sealed-bid-sourcing/
  README.md
  LICENSE
  AGENTS.md
  .gitignore
  specs/
    0001-foundation/
      requirements.md
      design.md
      tasks.md
      acceptance.md
  docs/
    first-pr.md
  paper/                 # arrives in PR 0002
  scenarios/             # benchmark instance JSON
  src/                   # arrives in PR 0002
```

## Why this exists

Mechanism-design academics have published PSI-based sealed-bid papers
(notably ScienceDirect Jan 2026) but no one with procurement-shape
test infrastructure has built a benchmark on top. The
`procurement-negotiation-lab` repo is a working multi-attribute
auction simulator with 12+ specs. It is the right launchpad. Adding
a sealed-bid scenario class plus an MPC reference runtime plus a
calibrated surplus-recovery-vs-unsealed-baseline dataset is the
artifact buyers and supplier coalitions cannot ignore.

## First artifact

A public benchmark plus CC-BY paper. Extend
`procurement-negotiation-lab` with a sealed-bid scenario class,
run on a 10-supplier 5-lot RFx, publish the leakage-bound proof plus
the surplus-recovery delta vs. an unsealed Coupa-style baseline.

## Compounds with

- `procurement-negotiation-lab` (the literal launchpad)
- `agent-notary-layer` (receipt schema cites the sealed-bid runtime
  as an audit-trail source)
- `supplier-risk-rag-agent` (eval discipline transfers to
  strategyproofness regression tests)

## License

MIT. See [LICENSE](LICENSE).
