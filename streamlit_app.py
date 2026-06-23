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

# ---------------------------------------------------------------------------
# Run the real sourcing engine live. The committed table above reads frozen
# receipts; the controls below call sealed_bid_sourcing.scoring.build_receipt
# — the same function that produced those receipts — on a scenario you edit.
# Change a lot's scoring weights or the suppliers' defensive markups and watch
# the winners, cleared prices and surplus delta recompute. Not a lookup.
# ---------------------------------------------------------------------------
st.divider()
st.subheader("run the auction yourself")
st.caption(
    "drive the actual clearing engine — `sealed_bid_sourcing.scoring.build_receipt` — "
    "on a scenario you edit. it re-runs the sealed and unsealed runtimes and recomputes "
    "every winner, cleared price and surplus number live."
)

try:
    import copy
    import sys

    sys.path.insert(0, str(ROOT))
    from sealed_bid_sourcing.model import HIGHER_IS_BETTER, validate_scenario_data
    from sealed_bid_sourcing.scoring import build_receipt

    base_scenario = json.loads((ROOT / "scenarios" / "v0_10x5.json").read_text(encoding="utf-8"))

    with st.expander("how it works", expanded=False):
        st.markdown(
            "- each lot ranks eligible suppliers by a weighted score over price, lead time, "
            "esg and quality (price + lead time are lower-is-better, esg + quality higher-is-better).\n"
            "- the **sealed** runtime scores the true submitted unit price.\n"
            "- the **unsealed** baseline first inflates each price by the supplier's defensive markup, "
            "then scores — so buyers clear at higher prices.\n"
            "- buyer surplus on a lot = (max willingness to pay − cleared price) × demand."
        )

    lot_choices = {lot["id"]: lot for lot in base_scenario["lots"]}
    sel_lot_id = st.selectbox(
        "tune a lot's scoring weights",
        list(lot_choices),
        format_func=lambda lid: f"{lid} — {lot_choices[lid]['name']}",
    )
    sel_lot = lot_choices[sel_lot_id]
    base_weights = sel_lot["scoring_weights"]

    st.caption(
        "set raw weights for the four criteria; they are renormalized to sum to 1.0 before scoring "
        "(price must stay > 0). this changes who wins this lot."
    )
    wc1, wc2, wc3, wc4 = st.columns(4)
    w_price = wc1.slider("price weight", 0.0, 1.0, float(base_weights.get("price", 0.0)), 0.05)
    w_lead = wc2.slider("lead-time weight", 0.0, 1.0, float(base_weights.get("lead_time_days", 0.0)), 0.05)
    w_esg = wc3.slider("esg weight", 0.0, 1.0, float(base_weights.get("esg_score", 0.0)), 0.05)
    w_qual = wc4.slider("quality weight", 0.0, 1.0, float(base_weights.get("quality_score", 0.0)), 0.05)

    markup_scale = st.slider(
        "defensive-markup multiplier (scales every supplier's unsealed markup)",
        0.0,
        2.0,
        1.0,
        0.1,
        help="0 = no defensive markup (sealed and unsealed converge); 2 = double the committed markups.",
    )

    raw = {"price": w_price, "lead_time_days": w_lead, "esg_score": w_esg, "quality_score": w_qual}
    raw = {k: v for k, v in raw.items() if v > 0}
    total_w = sum(raw.values())

    if w_price <= 0:
        st.error("price weight must be > 0 — the scoring engine requires a price weight on every lot.")
    elif total_w <= 0:
        st.error("at least one weight must be positive.")
    elif not any(k in (HIGHER_IS_BETTER | {"lead_time_days"}) for k in raw):
        st.error("add at least one non-price weight (lead time, esg or quality).")
    else:
        new_weights = {k: round(v / total_w, 6) for k, v in raw.items()}
        # nudge rounding so weights sum to exactly 1.0 (engine asserts within 0.001)
        drift = round(1.0 - sum(new_weights.values()), 6)
        first_key = next(iter(new_weights))
        new_weights[first_key] = round(new_weights[first_key] + drift, 6)

        edited = copy.deepcopy(base_scenario)
        for lot in edited["lots"]:
            if lot["id"] == sel_lot_id:
                lot["scoring_weights"] = new_weights
        for supplier in edited["suppliers"]:
            supplier["defensive_markup_pct"] = round(
                min(1.0, supplier.get("defensive_markup_pct", 0.0) * markup_scale), 6
            )

        errors = validate_scenario_data(edited)
        if errors:
            st.error("edited scenario is invalid: " + "; ".join(errors))
        else:
            sealed_r = build_receipt(edited, "sealed")
            unsealed_r = build_receipt(edited, "unsealed")

            d_buyer = round(sealed_r["surplus"]["buyer"] - unsealed_r["surplus"]["buyer"], 2)
            d_total = round(sealed_r["surplus"]["total"] - unsealed_r["surplus"]["total"], 2)

            st.markdown(f"**normalized weights for {sel_lot_id}:** " + ", ".join(f"{k} {v}" for k, v in new_weights.items()))

            r1, r2, r3 = st.columns(3)
            r1.metric("buyer surplus (sealed)", f"{sealed_r['surplus']['buyer']:,.0f}")
            r2.metric("buyer surplus gain vs unsealed", f"{d_buyer:,.0f}")
            r3.metric("total surplus delta", f"{d_total:,.0f}")

            s_by_lot = {a["lot_id"]: a for a in sealed_r["assignments"]}
            u_by_lot = {a["lot_id"]: a for a in unsealed_r["assignments"]}
            live_rows = []
            for lot_id in sorted(s_by_lot):
                s = s_by_lot[lot_id]
                u = u_by_lot[lot_id]
                live_rows.append(
                    {
                        "lot": lot_id + (" *" if lot_id == sel_lot_id else ""),
                        "sealed winner": s["supplier_id"],
                        "sealed price": s["cleared_unit_price"],
                        "unsealed winner": u["supplier_id"],
                        "unsealed price": u["cleared_unit_price"],
                        "buyer surplus gain": round((s["buyer_surplus"] or 0) - (u["buyer_surplus"] or 0), 2),
                    }
                )
            st.dataframe(pd.DataFrame(live_rows), use_container_width=True, hide_index=True)

            sel_s = s_by_lot[sel_lot_id]
            base_s = sealed_by_lot.get(sel_lot_id, {})
            if sel_s["supplier_id"] != base_s.get("supplier_id"):
                st.success(
                    f"your weights flipped the sealed winner on {sel_lot_id} from "
                    f"{base_s.get('supplier_id')} to {sel_s['supplier_id']} "
                    f"(cleared {sel_s['cleared_unit_price']}). this is the live engine re-clearing the lot, not a lookup."
                )
            else:
                st.caption(
                    f"sealed winner on {sel_lot_id} is {sel_s['supplier_id']} at {sel_s['cleared_unit_price']}. "
                    "push the weights further, or drop the markup multiplier toward 0 to collapse the sealed/unsealed gap."
                )
            st.caption(
                f"receipt ids recomputed live: `{sealed_r['receipt_id']}` / `{unsealed_r['receipt_id']}` — "
                "both produced by build_receipt on your edited scenario."
            )
except Exception as exc:  # pragma: no cover - defensive for cloud import differences
    st.info(f"interactive auction needs the package importable ({exc}). the committed comparison above still renders.")

st.caption(
    "the clearing + surplus logic lives in `sealed_bid_sourcing/scoring.py`; the top table reads the "
    "committed `runs/*/receipt.json`, and the controls above are the real engine re-running on your edits. "
    "repo: github.com/AthenaTheOwl/sealed-bid-sourcing"
)
