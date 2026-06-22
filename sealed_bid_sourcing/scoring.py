from __future__ import annotations

from pathlib import Path
from typing import Any

from .model import (
    GENERATED_AT,
    LOWER_IS_BETTER,
    RUNTIME_VERSION,
    assert_valid_scenario,
    hash_payload,
    load_json,
    scenario_hash,
    validate_receipt_data,
    write_json,
)


def supplier_index(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {supplier["id"]: supplier for supplier in scenario["suppliers"]}


def lot_index(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {lot["id"]: lot for lot in scenario["lots"]}


def runtime_price(bid: dict[str, Any], supplier: dict[str, Any], runtime: str) -> float:
    if runtime == "unsealed":
        return round(bid["unit_price"] * (1.0 + supplier.get("defensive_markup_pct", 0.0)), 2)
    return round(bid["unit_price"], 2)


def normalize(value: float, values: list[float], lower_is_better: bool) -> float:
    low = min(values)
    high = max(values)
    if high == low:
        return 1.0
    if lower_is_better:
        return (high - value) / (high - low)
    return (value - low) / (high - low)


def eligible_bids(
    scenario: dict[str, Any],
    lot: dict[str, Any],
    suppliers: dict[str, dict[str, Any]],
    runtime: str,
) -> list[dict[str, Any]]:
    lot_id = lot["id"]
    demand = lot["demand"]
    reserve = lot.get("reserve_unit_price")
    candidates: list[dict[str, Any]] = []
    for bid in scenario["bids"]:
        if bid["lot_id"] != lot_id:
            continue
        supplier = suppliers[bid["supplier_id"]]
        if supplier["capacity"].get(lot_id, 0) < demand:
            continue
        price = runtime_price(bid, supplier, runtime)
        if reserve is not None and price > reserve:
            continue
        candidate = dict(bid)
        candidate["runtime_unit_price"] = price
        candidates.append(candidate)
    return candidates


def score_candidates(candidates: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
    if not candidates:
        return []
    metric_values = {
        "price": [candidate["runtime_unit_price"] for candidate in candidates],
        "lead_time_days": [candidate["lead_time_days"] for candidate in candidates],
        "esg_score": [candidate["esg_score"] for candidate in candidates],
        "quality_score": [candidate["quality_score"] for candidate in candidates],
    }
    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        score = 0.0
        for key, weight in weights.items():
            raw = candidate["runtime_unit_price"] if key == "price" else candidate[key]
            score += weight * normalize(raw, metric_values[key], key in LOWER_IS_BETTER)
        scored_candidate = dict(candidate)
        scored_candidate["score"] = round(score, 6)
        scored.append(scored_candidate)
    return sorted(scored, key=lambda item: (-item["score"], item["runtime_unit_price"], item["supplier_id"]))


def build_receipt(scenario: dict[str, Any], runtime: str) -> dict[str, Any]:
    if runtime not in {"sealed", "unsealed"}:
        raise ValueError("runtime must be sealed or unsealed")
    assert_valid_scenario(scenario)
    suppliers = supplier_index(scenario)
    scenario_digest = scenario_hash(scenario)
    assignments: list[dict[str, Any]] = []
    buyer_surplus = 0.0
    supplier_surplus = 0.0

    for lot in scenario["lots"]:
        candidates = eligible_bids(scenario, lot, suppliers, runtime)
        scored = score_candidates(candidates, lot["scoring_weights"])
        if not scored:
            assignments.append(
                {
                    "lot_id": lot["id"],
                    "supplier_id": None,
                    "quantity": lot["demand"],
                    "cleared_unit_price": None,
                    "opened_bid": None,
                    "score": None,
                    "buyer_surplus": 0.0,
                    "supplier_surplus": 0.0,
                    "total_surplus": 0.0,
                    "status": "unassigned",
                }
            )
            continue

        winner = scored[0]
        cleared_unit_price = winner["runtime_unit_price"]
        quantity = lot["demand"]
        lot_buyer_surplus = round((lot["max_willingness_to_pay"] - cleared_unit_price) * quantity, 2)
        lot_supplier_surplus = round((cleared_unit_price - winner["true_unit_cost"]) * quantity, 2)
        buyer_surplus += lot_buyer_surplus
        supplier_surplus += lot_supplier_surplus
        assignments.append(
            {
                "lot_id": lot["id"],
                "supplier_id": winner["supplier_id"],
                "quantity": quantity,
                "cleared_unit_price": cleared_unit_price,
                "opened_bid": {
                    "unit_price": cleared_unit_price,
                    "sealed_unit_price": winner["unit_price"],
                    "true_unit_cost": winner["true_unit_cost"],
                    "lead_time_days": winner["lead_time_days"],
                    "esg_score": winner["esg_score"],
                    "quality_score": winner["quality_score"],
                },
                "score": winner["score"],
                "buyer_surplus": lot_buyer_surplus,
                "supplier_surplus": lot_supplier_surplus,
                "total_surplus": round(lot_buyer_surplus + lot_supplier_surplus, 2),
                "status": "assigned",
            }
        )

    commitments = []
    for supplier in scenario["suppliers"]:
        supplier_bids = [
            bid for bid in scenario["bids"] if bid["supplier_id"] == supplier["id"]
        ]
        commitments.append(
            {
                "supplier_id": supplier["id"],
                "commitment_hash": hash_payload(
                    {
                        "scenario_hash": scenario_digest,
                        "supplier_id": supplier["id"],
                        "bids": supplier_bids,
                    }
                ),
            }
        )

    leakage_profile = (
        "winner ids, opened winning bids, per-lot scores, commitments, scenario hash"
        if runtime == "sealed"
        else "all submitted bid prices visible to buyer-side baseline"
    )
    receipt = {
        "receipt_id": f"{scenario['scenario_id']}-{runtime}-v{RUNTIME_VERSION}",
        "scenario_id": scenario["scenario_id"],
        "scenario_hash": scenario_digest,
        "runtime": runtime,
        "runtime_version": RUNTIME_VERSION,
        "generated_at": GENERATED_AT,
        "auction_rule": scenario["auction_rule"],
        "commitments": commitments,
        "assignments": assignments,
        "surplus": {
            "buyer": round(buyer_surplus, 2),
            "supplier": round(supplier_surplus, 2),
            "total": round(buyer_surplus + supplier_surplus, 2),
        },
        "leakage_profile": leakage_profile,
    }
    receipt_errors = validate_receipt_data(receipt)
    if receipt_errors:
        raise ValueError("; ".join(receipt_errors))
    return receipt


def write_receipt(scenario_path: str | Path, runtime: str, out_dir: str | Path) -> Path:
    scenario = load_json(scenario_path)
    receipt = build_receipt(scenario, runtime)
    out_path = Path(out_dir) / "receipt.json"
    write_json(out_path, receipt)
    return out_path


def write_surplus_report(sealed_path: str | Path, unsealed_path: str | Path, out_path: str | Path) -> Path:
    sealed = load_json(sealed_path)
    unsealed = load_json(unsealed_path)
    for name, receipt in [("sealed", sealed), ("unsealed", unsealed)]:
        errors = validate_receipt_data(receipt)
        if errors:
            raise ValueError(f"{name} receipt invalid: {'; '.join(errors)}")

    delta_buyer = round(sealed["surplus"]["buyer"] - unsealed["surplus"]["buyer"], 2)
    delta_supplier = round(sealed["surplus"]["supplier"] - unsealed["surplus"]["supplier"], 2)
    delta_total = round(sealed["surplus"]["total"] - unsealed["surplus"]["total"], 2)

    sealed_by_lot = {assignment["lot_id"]: assignment for assignment in sealed["assignments"]}
    unsealed_by_lot = {assignment["lot_id"]: assignment for assignment in unsealed["assignments"]}
    rows = []
    for lot_id in sorted(sealed_by_lot):
        s = sealed_by_lot[lot_id]
        u = unsealed_by_lot[lot_id]
        rows.append(
            "| {lot} | {sw} | {sp} | {uw} | {up} | {dt:.2f} |".format(
                lot=lot_id,
                sw=s["supplier_id"],
                sp=s["cleared_unit_price"],
                uw=u["supplier_id"],
                up=u["cleared_unit_price"],
                dt=round(s["total_surplus"] - u["total_surplus"], 2),
            )
        )

    report = "\n".join(
        [
            "# Surplus Delta Report",
            "",
            f"Scenario: `{sealed['scenario_id']}`",
            f"Sealed receipt: `{sealed['receipt_id']}`",
            f"Unsealed receipt: `{unsealed['receipt_id']}`",
            "",
            "## Headline",
            "",
            f"- Buyer surplus delta: `{delta_buyer:.2f}`",
            f"- Supplier surplus delta: `{delta_supplier:.2f}`",
            f"- Total surplus delta: `{delta_total:.2f}`",
            "",
            "## Runtime Totals",
            "",
            "| Runtime | Buyer surplus | Supplier surplus | Total surplus |",
            "|---|---:|---:|---:|",
            f"| sealed | {sealed['surplus']['buyer']:.2f} | {sealed['surplus']['supplier']:.2f} | {sealed['surplus']['total']:.2f} |",
            f"| unsealed | {unsealed['surplus']['buyer']:.2f} | {unsealed['surplus']['supplier']:.2f} | {unsealed['surplus']['total']:.2f} |",
            "",
            "## Assignment Comparison",
            "",
            "| Lot | Sealed winner | Sealed price | Unsealed winner | Unsealed price | Total delta |",
            "|---|---|---:|---|---:|---:|",
            *rows,
            "",
            "The sealed run keeps losing bid values out of the buyer-side receipt.",
            "The unsealed baseline applies the scenario's defensive markups before scoring.",
            "",
        ]
    )
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    return target
