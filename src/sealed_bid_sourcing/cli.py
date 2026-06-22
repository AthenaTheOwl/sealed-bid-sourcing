from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

RUNTIME_VERSION = "0.1.0"
GENERATED_AT = "2026-06-22T00:00:00Z"
LOWER_IS_BETTER = {"price", "lead_time_days"}
HIGHER_IS_BETTER = {"esg_score", "quality_score"}
WEIGHT_KEYS = LOWER_IS_BETTER | HIGHER_IS_BETTER


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scenario_hash(scenario: dict[str, Any]) -> str:
    encoded = json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_scenario_data(scenario: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {"scenario_id", "auction_rule", "currency", "suppliers", "lots", "bids"}
    missing = sorted(required - set(scenario))
    if missing:
        errors.append(f"missing root fields: {', '.join(missing)}")
        return errors

    if scenario["auction_rule"] not in {"first-price-sealed", "vickrey-sealed"}:
        errors.append("auction_rule must be first-price-sealed or vickrey-sealed")

    suppliers = scenario.get("suppliers", [])
    lots = scenario.get("lots", [])
    bids = scenario.get("bids", [])
    if len(suppliers) < 2:
        errors.append("scenario must include at least two suppliers")
    if len(lots) < 1:
        errors.append("scenario must include at least one lot")

    supplier_ids = [supplier.get("id") for supplier in suppliers]
    lot_ids = [lot.get("id") for lot in lots]
    if len(supplier_ids) != len(set(supplier_ids)):
        errors.append("supplier ids must be unique")
    if len(lot_ids) != len(set(lot_ids)):
        errors.append("lot ids must be unique")
    supplier_set = set(supplier_ids)
    lot_set = set(lot_ids)

    for supplier in suppliers:
        sid = supplier.get("id", "<missing>")
        capacity = supplier.get("capacity", {})
        if not isinstance(capacity, dict):
            errors.append(f"supplier {sid} capacity must be an object")
            continue
        for lot_id in lot_ids:
            if lot_id not in capacity:
                errors.append(f"supplier {sid} missing capacity for {lot_id}")
            elif capacity[lot_id] < 0:
                errors.append(f"supplier {sid} has negative capacity for {lot_id}")
        markup = supplier.get("defensive_markup_pct", 0)
        if markup < 0 or markup > 1:
            errors.append(f"supplier {sid} defensive_markup_pct must be between 0 and 1")

    for lot in lots:
        lot_id = lot.get("id", "<missing>")
        if lot.get("demand", 0) <= 0:
            errors.append(f"lot {lot_id} demand must be positive")
        weights = lot.get("scoring_weights", {})
        if not weights:
            errors.append(f"lot {lot_id} must define scoring_weights")
            continue
        unknown_weights = sorted(set(weights) - WEIGHT_KEYS)
        if unknown_weights:
            errors.append(f"lot {lot_id} has unknown scoring weights: {', '.join(unknown_weights)}")
        if "price" not in weights:
            errors.append(f"lot {lot_id} scoring_weights must include price")
        if not any(key in weights for key in HIGHER_IS_BETTER | {"lead_time_days"}):
            errors.append(f"lot {lot_id} must include at least one non-price scoring weight")
        if abs(sum(weights.values()) - 1.0) > 0.001:
            errors.append(f"lot {lot_id} scoring weights must sum to 1.0")
        reserve = lot.get("reserve_unit_price")
        max_wtp = lot.get("max_willingness_to_pay")
        if reserve is not None and reserve <= 0:
            errors.append(f"lot {lot_id} reserve_unit_price must be positive")
        if max_wtp is None or max_wtp <= 0:
            errors.append(f"lot {lot_id} max_willingness_to_pay must be positive")

    seen_pairs: set[tuple[str, str]] = set()
    for bid in bids:
        sid = bid.get("supplier_id")
        lot_id = bid.get("lot_id")
        if sid not in supplier_set:
            errors.append(f"bid references unknown supplier {sid}")
        if lot_id not in lot_set:
            errors.append(f"bid references unknown lot {lot_id}")
        pair = (sid, lot_id)
        if pair in seen_pairs:
            errors.append(f"duplicate bid for supplier {sid} lot {lot_id}")
        seen_pairs.add(pair)
        for field in ["unit_price", "true_unit_cost", "lead_time_days", "esg_score", "quality_score"]:
            if field not in bid:
                errors.append(f"bid {sid}/{lot_id} missing {field}")
            elif bid[field] < 0:
                errors.append(f"bid {sid}/{lot_id} {field} must be non-negative")
        if bid.get("true_unit_cost", 0) > bid.get("unit_price", 0):
            errors.append(f"bid {sid}/{lot_id} true_unit_cost cannot exceed unit_price")

    for lot_id in lot_ids:
        if not any(bid.get("lot_id") == lot_id for bid in bids):
            errors.append(f"lot {lot_id} has no bids")

    return errors


def _assert_valid_scenario(scenario: dict[str, Any]) -> None:
    errors = validate_scenario_data(scenario)
    if errors:
        raise ValueError("; ".join(errors))


def validate_receipt_data(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "receipt_id",
        "scenario_id",
        "scenario_hash",
        "runtime",
        "runtime_version",
        "commitments",
        "assignments",
        "surplus",
        "leakage_profile",
    }
    missing = sorted(required - set(receipt))
    if missing:
        errors.append(f"missing receipt fields: {', '.join(missing)}")
        return errors
    if receipt["runtime"] not in {"sealed", "unsealed"}:
        errors.append("runtime must be sealed or unsealed")
    if not str(receipt["scenario_hash"]).startswith("sha256:"):
        errors.append("scenario_hash must be a sha256 digest")
    surplus = receipt.get("surplus", {})
    for field in ["buyer", "supplier", "total"]:
        if field not in surplus:
            errors.append(f"surplus missing {field}")
    for assignment in receipt.get("assignments", []):
        for field in ["lot_id", "supplier_id", "quantity", "cleared_unit_price", "opened_bid", "score"]:
            if field not in assignment:
                errors.append(f"assignment missing {field}")
    return errors


def _supplier_index(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {supplier["id"]: supplier for supplier in scenario["suppliers"]}


def _lot_index(scenario: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {lot["id"]: lot for lot in scenario["lots"]}


def _runtime_price(bid: dict[str, Any], supplier: dict[str, Any], runtime: str) -> float:
    if runtime == "unsealed":
        return round(bid["unit_price"] * (1.0 + supplier.get("defensive_markup_pct", 0.0)), 2)
    return round(bid["unit_price"], 2)


def _normalize(value: float, values: list[float], lower_is_better: bool) -> float:
    low = min(values)
    high = max(values)
    if high == low:
        return 1.0
    if lower_is_better:
        return (high - value) / (high - low)
    return (value - low) / (high - low)


def _eligible_bids(
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
        price = _runtime_price(bid, supplier, runtime)
        if reserve is not None and price > reserve:
            continue
        candidate = dict(bid)
        candidate["runtime_unit_price"] = price
        candidates.append(candidate)
    return candidates


def _score_candidates(candidates: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
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
            score += weight * _normalize(raw, metric_values[key], key in LOWER_IS_BETTER)
        scored_candidate = dict(candidate)
        scored_candidate["score"] = round(score, 6)
        scored.append(scored_candidate)
    return sorted(scored, key=lambda item: (-item["score"], item["runtime_unit_price"], item["supplier_id"]))


def build_receipt(scenario: dict[str, Any], runtime: str) -> dict[str, Any]:
    if runtime not in {"sealed", "unsealed"}:
        raise ValueError("runtime must be sealed or unsealed")
    _assert_valid_scenario(scenario)
    suppliers = _supplier_index(scenario)
    scenario_digest = scenario_hash(scenario)
    assignments: list[dict[str, Any]] = []
    buyer_surplus = 0.0
    supplier_surplus = 0.0

    for lot in scenario["lots"]:
        candidates = _eligible_bids(scenario, lot, suppliers, runtime)
        scored = _score_candidates(candidates, lot["scoring_weights"])
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
                "commitment_hash": _hash_payload(
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


def _cmd_validate(args: argparse.Namespace) -> int:
    failures: list[str] = []
    for path_text in args.paths:
        path = Path(path_text)
        paths = sorted(path.rglob("*.json")) if path.is_dir() else [path]
        for json_path in paths:
            payload = load_json(json_path)
            if "scenario_id" in payload and "lots" in payload and "bids" in payload:
                errors = validate_scenario_data(payload)
            elif "receipt_id" in payload:
                errors = validate_receipt_data(payload)
            else:
                errors = []
            if errors:
                failures.append(f"{json_path}: {'; '.join(errors)}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("OK")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    out_path = write_receipt(args.scenario, args.runtime, args.out)
    print(out_path)
    return 0


def _cmd_surplus_delta(args: argparse.Namespace) -> int:
    out_path = write_surplus_report(args.sealed, args.unsealed, args.out)
    print(out_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sealed_bid_sourcing")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate scenarios or receipts")
    validate.add_argument("paths", nargs="+")
    validate.set_defaults(func=_cmd_validate)

    run = subcommands.add_parser("run", help="run a reference runtime")
    run.add_argument("--scenario", required=True)
    run.add_argument("--runtime", choices=["sealed", "unsealed"], required=True)
    run.add_argument("--out", required=True)
    run.set_defaults(func=_cmd_run)

    surplus = subcommands.add_parser("surplus-delta", help="write a surplus delta report")
    surplus.add_argument("--sealed", required=True)
    surplus.add_argument("--unsealed", required=True)
    surplus.add_argument("--out", required=True)
    surplus.set_defaults(func=_cmd_surplus_delta)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
