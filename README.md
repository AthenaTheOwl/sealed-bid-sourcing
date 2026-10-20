# sealed-bid-sourcing

On lot L4, supplier S07 can clear at 9.50. The unsealed baseline assumes every
supplier pads its bid by a fixed `defensive_markup_pct` taken from the scenario:
20% for S07, 4% for S02, 3% to 20% across the ten suppliers in
`scenarios/v0_10x5.json`. Under that assumption S07's 9.50 becomes 11.40, over
the lot's 10.70 reserve, and S02 wins at 10.61: the buyer pays 1.11 more per
unit, 777 on the lot. Across five lots the modeled markups cost the buyer 2,259
in surplus. That number is a model result, conditional on the assumed markups.
It says nothing measured about real suppliers: set every `defensive_markup_pct`
to 0 and the gap is 0.00, which the zero-markup control in
`reports/surplus_delta.md` shows. This repo measures what that assumed padding
costs the buyer when the losing bids never leave the envelope.

## What it does

A reverse auction asks suppliers to bid down a price. The benchmark assumes that
when bids are visible, suppliers price against each other's room to move and add
a defensive markup on top of the bid they would have sealed. The unsealed runtime
encodes that assumption as each supplier's `defensive_markup_pct`, applied before
scoring; the repo takes the values as inputs and does not estimate them from
supplier data. A sealed runtime opens only the winning bids in the buyer-side
receipt. The losing values, the losing order book, every supplier's true cost,
winners included: none of it leaves the envelope. One thing about the losing bids
does: each published per-lot score is min-max normalized over every eligible bid
on the lot, so it moves with the range of the losing bids.

sealed-bid-sourcing runs two matched benchmarks both ways: a ten-supplier, five-lot
case and a twenty-supplier, ten-lot case. It reports the surplus delta for each,
next to a zero-markup control that shows how much of it the markup produces.
The sealed runtime's receipt exposes a fixed
list of fields and nothing else: scenario hash, winner ids, opened winning bids
(price, lead time, ESG and quality, never cost), per-lot scores, commitment
hashes, plus the buyer's own lot terms and buyer surplus. A gate
(`scripts/validate_leakage_bound.py`, run in CI) opens every receipt under `runs/`
and fails the build if a field shows up that `paper/leakage_bounds.yaml` does not
map to allowed leakage. Losing bids, every supplier's true cost and supplier
surplus are disallowed leakage. The surplus report still needs the last two, so
they sit in an `internal_audit.json` next to each receipt, outside what the buyer
sees.

v0.1 is a reference benchmark, not production MPC. The sealed scorer stands in for
the secret-sharing and PSI primitives it cites; the receipt schema is the part
that's load-bearing, and the leakage gate guards it.

## Try it

Print the committed sealed-vs-unsealed comparison from the terminal:

```bash
python -m sealed_bid_sourcing show
python -m sealed_bid_sourcing show \
  --sealed runs/sealed_v1/receipt.json \
  --unsealed runs/unsealed_v1/receipt.json
```

```
scenario: v0_10x5  (auction rule: first-price-sealed)
sealed vs unsealed runtime, 5 lots

buyer surplus per runtime
  sealed    13,430.00
  unsealed  11,171.00

lot  sealed win     price  unsealed win     price    buyer gain
---------------------------------------------------------------
L4   S07             9.50  S02              10.61        777.00
L1   S07            11.70  S08              12.57        696.00
L5   S08            30.80  S08              31.72        368.00
L2   S08            18.80  S08              19.36        280.00
L3   S08            23.90  S02              24.13        138.00

headline: sealing bids returns +2,259.00 buyer surplus vs the unsealed markup baseline (total surplus delta +640.00).
          biggest single-lot gain is L4: +777.00 buyer surplus, where unsealed defensive markups push the cleared price from 9.50 to 10.61.
```

Ranked by buyer gain, biggest recovered surplus first. It reads the committed
receipts under `runs/` — offline, read-only.

## Live demo

Run the interactive browser locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Both read the committed receipts under `runs/` directly (offline, read-only).

deploy on Streamlit Cloud: repo `AthenaTheOwl/sealed-bid-sourcing`, branch `main`,
main file `streamlit_app.py`.

<!-- live url: (add Streamlit Cloud URL here after deploy) -->

## How it connects

The procurement cluster works the same supplier graph from different angles:

- [procurement-negotiation-lab](https://github.com/AthenaTheOwl/procurement-negotiation-lab)
  — the surplus left on the table when two parties fail to coordinate a deal, the
  same gap this repo closes by sealing the bids.
- [procurement-pattern-library](https://github.com/AthenaTheOwl/procurement-pattern-library)
  — the recurring single-source and fallback shapes that make a sealed auction
  worth running in the first place.
- [source-decay-ledger](https://github.com/AthenaTheOwl/source-decay-ledger) — the
  upstream feed: which sources still earn their place before they reach a sourcing
  decision.

## How to run

```bash
python -m uv run pytest
python -m uv run python scripts/voice_lint.py paper/ README.md
python -m uv run python scripts/validate_schemas.py schemas/ scenarios/ runs/
python -m uv run python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml --runtime sealed
python -m uv run python scripts/validate_leakage_bound.py paper/leakage_bounds.yaml --runtime unsealed
python -m uv run python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
python -m uv run python -m sealed_bid_sourcing validate scenarios/v1_20x10.json
```

To regenerate the checked-in run artifacts:

```bash
python -m uv run python -m sealed_bid_sourcing run \
  --scenario scenarios/v0_10x5.json \
  --runtime sealed \
  --out runs/sealed_v0/

python -m uv run python -m sealed_bid_sourcing run \
  --scenario scenarios/v0_10x5.json \
  --runtime unsealed \
  --out runs/unsealed_v0/

python -m uv run python -m sealed_bid_sourcing surplus-delta \
  --scenario scenarios/v0_10x5.json \
  --sealed runs/sealed_v0/receipt.json \
  --unsealed runs/unsealed_v0/receipt.json \
  --out reports/surplus_delta.md
```

Without uv, the package also runs from a local editable install:

```bash
python -m pytest
python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
```

## Layout

```text
sealed-bid-sourcing/
  docs/
    product-brief.md
    system-map.md
  specs/
    0001-foundation/
    0002-design/
  schemas/
    scenario.schema.json
    receipt.schema.json
  scenarios/
    v0_10x5.json
    v1_20x10.json
  src/sealed_bid_sourcing/
  scripts/
  tests/
  runs/
  reports/
  paper/
  decisions/
  STATUS.md
```

## Method update

[October method update: A modeled markup difference is a conditional result](docs/surplus-and-disclosure-experiment.md).

## License

MIT. See [LICENSE](LICENSE).
