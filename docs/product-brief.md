# Product Brief

## Problem

Buyer-side sourcing agents can compare and negotiate against disclosed bids.
That gives suppliers a reason to shade prices instead of submitting their best
offer. Reverse auctions then lose the strategyproofness that made them useful.

## v0.1 Artifact

Sealed Bid Sourcing v0.1 is a data-report repo. It ships:

- A typed 10 supplier, 5 lot benchmark scenario.
- A sealed reference runtime that opens only winning bids.
- An unsealed baseline that applies defensive supplier markup before scoring.
- A receipt schema for audit output.
- A checked-in surplus delta report.
- A paper skeleton and leakage-bound file that name the security surface.

## User

The primary user is a procurement researcher or platform engineer evaluating
whether sealed bid handling changes surplus recovery under a multi-attribute
reverse auction.

## Non-Goals

- Production MPC throughput.
- Native Coupa, Zip, or Ariba integration.
- On-chain settlement.
- Forward-auction variants.
