"""sealed-bid sourcing: sealed vs unsealed surplus browser.

reads the committed receipts under runs/ directly. no network, no secrets.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SEALED = ROOT / "runs" / "sealed_v0" / "receipt.json"
UNSEALED = ROOT / "runs" / "unsealed_v0" / "receipt.json"


def load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


st.set_page_config(page_title="sealed-bid sourcing", layout="wide")
st.title("sealed-bid sourcing")
st.caption(
    "sealed receipt-producing runtime vs an unsealed markup baseline, "
    "on the same 10-supplier / 5-lot reverse-procurement scenario."
)

sealed = load(SEALED)
unsealed = load(UNSEALED)
if sealed is None or unsealed is None:
    st.warning(
        "committed receipts not found under runs/. generate them with "
        "`python -m sealed_bid_sourcing run ...` and commit the output."
    )
    st.stop()

buyer_delta = round(sealed["surplus"]["buyer"] - unsealed["surplus"]["buyer"], 2)
supplier_delta = round(sealed["surplus"]["supplier"] - unsealed["surplus"]["supplier"], 2)
total_delta = round(sealed["surplus"]["total"] - unsealed["surplus"]["total"], 2)

c1, c2, c3 = st.columns(3)
c1.metric("buyer surplus gain (sealed - unsealed)", f"{buyer_delta:,.0f}")
c2.metric("supplier surplus delta", f"{supplier_delta:,.0f}")
c3.metric("total surplus delta", f"{total_delta:,.0f}")

sealed_by_lot = {a["lot_id"]: a for a in sealed["assignments"]}
unsealed_by_lot = {a["lot_id"]: a for a in unsealed["assignments"]}
rows = []
for lot_id in sorted(sealed_by_lot):
    s = sealed_by_lot[lot_id]
    u = unsealed_by_lot[lot_id]
    rows.append(
        {
            "lot": lot_id,
            "sealed winner": s["supplier_id"],
            "sealed price": s["cleared_unit_price"],
            "unsealed winner": u["supplier_id"],
            "unsealed price": u["cleared_unit_price"],
            "buyer surplus gain": round(s["buyer_surplus"] - u["buyer_surplus"], 2),
            "total surplus delta": round(s["total_surplus"] - u["total_surplus"], 2),
        }
    )
df = pd.DataFrame(rows).sort_values("buyer surplus gain", ascending=False).reset_index(drop=True)

sort_choice = st.radio(
    "rank lots by",
    ["buyer surplus gain", "total surplus delta", "lot"],
    horizontal=True,
)
shown = df.sort_values(sort_choice, ascending=(sort_choice == "lot")).reset_index(drop=True)
st.dataframe(shown, use_container_width=True)

top = df.iloc[0]
st.info(
    f"sealing bids returns +{buyer_delta:,.0f} buyer surplus versus the unsealed markup baseline. "
    f"the biggest single-lot gain is {top['lot']}: +{top['buyer surplus gain']:,.0f} buyer surplus, "
    f"where unsealed defensive markups raise the cleared price from "
    f"{top['sealed price']:.2f} to {top['unsealed price']:.2f}."
)
