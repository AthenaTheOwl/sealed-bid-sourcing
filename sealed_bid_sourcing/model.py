from __future__ import annotations

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


def hash_payload(payload: Any) -> str:
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


def assert_valid_scenario(scenario: dict[str, Any]) -> None:
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
