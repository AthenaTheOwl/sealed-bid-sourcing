from collections import Counter
from pathlib import Path

from sealed_bid_sourcing import build_receipt, load_json, write_receipt


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "v1_20x10.json"


def test_v1_scenario_shape() -> None:
    scenario = load_json(SCENARIO)

    assert scenario["scenario_id"] == "v1_20x10"
    assert len(scenario["suppliers"]) == 20
    assert len(scenario["lots"]) == 10
    assert len(scenario["bids"]) == 100

    bids_per_lot = Counter(bid["lot_id"] for bid in scenario["bids"])
    assert set(bids_per_lot) == {lot["id"] for lot in scenario["lots"]}
    assert all(count >= 2 for count in bids_per_lot.values())


def test_v1_sealed_winners_and_surplus_are_pinned() -> None:
    scenario = load_json(SCENARIO)
    sealed = build_receipt(scenario, "sealed")

    winners = [(assignment["lot_id"], assignment["supplier_id"]) for assignment in sealed["assignments"]]
    assert winners == [
        ("L1", "S07"),
        ("L2", "S08"),
        ("L3", "S03"),
        ("L4", "S07"),
        ("L5", "S08"),
        ("L6", "S17"),
        ("L7", "S18"),
        ("L8", "S13"),
        ("L9", "S17"),
        ("L10", "S18"),
    ]
    assert sealed["surplus"]["buyer"] == 54173.0


def test_v1_sealed_runtime_is_deterministic(tmp_path) -> None:
    left_path = write_receipt(SCENARIO, "sealed", tmp_path / "left")
    right_path = write_receipt(SCENARIO, "sealed", tmp_path / "right")

    left = load_json(left_path)
    right = load_json(right_path)
    left.pop("generated_at", None)
    right.pop("generated_at", None)

    assert left == right
