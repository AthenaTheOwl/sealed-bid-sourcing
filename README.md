# sealed-bid-sourcing

On lot L4, supplier S07 can clear at 9.50. Run the same auction unsealed, where
suppliers see room to pad, and the lot clears at 10.61 with a different winner.
That 1.11 per unit is 777 the buyer never had to spend. Across five lots the
unsealed markups cost the buyer 2,259 in surplus. This repo measures exactly that
gap: what the buyer keeps when the losing bids never leave the envelope.

## What it does

A reverse auction asks suppliers to bid down a price. The trouble is that when
bids are visible, suppliers price against each other's room to move, not against
their own cost — they add a defensive markup and pocket the slack. A sealed
runtime opens only the winning bids in the buyer-side receipt. The losing values,
the losing order book, the true costs behind the losers: none of it leaves the
envelope.

sealed-bid-sourcing runs one canonical scenario — ten suppliers, five lots — both
ways and reports the surplus delta. The sealed runtime's receipt exposes a fixed
list of fields and nothing else: scenario hash, winner ids, opened winning bids,
per-lot scores, commitment hashes. A gate (`scripts/validate_leakage_bound.py`)
fails the build if a field outside that list shows up. The losing bids are
disallowed leakage, and the test enforces it.

v0.1 is a reference benchmark, not production MPC. The sealed scorer stands in for
the secret-sharing and PSI primitives it cites; the receipt schema is the part
that's load-bearing, and the leakage gate guards it.

## Try it

Print the committed sealed-vs-unsealed comparison from the terminal:

```bash
python -m sealed_bid_sourcing show
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
python -m uv run python -m sealed_bid_sourcing validate scenarios/v0_10x5.json
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
  src/sealed_bid_sourcing/
  scripts/
  tests/
  runs/
  reports/
  paper/
  decisions/
  STATUS.md
```

## License

MIT. See [LICENSE](LICENSE).
