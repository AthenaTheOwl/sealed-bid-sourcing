import copy
import shutil
from pathlib import Path

from sealed_bid_sourcing import (
    build_internal_audit,
    build_receipt,
    load_json,
    validate_receipt_data,
    validate_scenario_data,
    write_receipt,
    write_surplus_report,
)
from sealed_bid_sourcing.cli import main


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "scenarios" / "v0_10x5.json"


def test_canonical_scenario_validates() -> None:
    scenario = load_json(SCENARIO)
    assert validate_scenario_data(scenario) == []
    assert len(scenario["suppliers"]) == 10
    assert len(scenario["lots"]) == 5
    assert scenario["suppliers"][0]["capacity"]["L2"] == 0


def test_cli_validate_uses_canonical_artifacts(capsys) -> None:
    assert main(["validate"]) == 0

    out = capsys.readouterr().out
    assert "OK" in out


def test_show_prints_ranked_comparison(capsys) -> None:
    assert main(["show"]) == 0

    out = capsys.readouterr().out
    assert "buyer surplus per runtime" in out
    assert "headline:" in out
    # ranked by buyer-surplus gain: L1 (+696) should print before L5 (+368)
    assert out.index("L1") < out.index("L5")
    # headline reports the committed buyer-surplus delta
    assert "+2,259.00 buyer surplus" in out


def test_reference_runtimes_emit_valid_receipts() -> None:
    scenario = load_json(SCENARIO)
    sealed = build_receipt(scenario, "sealed")
    unsealed = build_receipt(scenario, "unsealed")

    assert validate_receipt_data(sealed) == []
    assert validate_receipt_data(unsealed) == []
    assert sealed["runtime"] == "sealed"
    assert unsealed["runtime"] == "unsealed"
    assert sealed["surplus"]["buyer"] > unsealed["surplus"]["buyer"]
    sealed_audit = build_internal_audit(scenario, "sealed")
    unsealed_audit = build_internal_audit(scenario, "unsealed")
    assert sealed_audit["surplus"]["total"] >= unsealed_audit["surplus"]["total"]


INTERNAL_KEYS = {"true_unit_cost", "sealed_unit_price", "supplier_surplus", "total_surplus"}


def _all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value))
    return set()


def test_receipts_carry_no_true_costs_or_supplier_surplus() -> None:
    # The buyer-facing receipt must not reveal any supplier's true cost, winners
    # included. Supplier surplus (margin x quantity) and total surplus give the
    # winner's cost back from the cleared price, so they stay out too.
    receipts = [load_json(path) for path in sorted((ROOT / "runs").glob("*/receipt.json"))]
    assert len(receipts) == 4
    for scenario_path in [SCENARIO, ROOT / "scenarios" / "v1_20x10.json"]:
        scenario = load_json(scenario_path)
        receipts += [build_receipt(scenario, "sealed"), build_receipt(scenario, "unsealed")]
    for receipt in receipts:
        assert _all_keys(receipt) & INTERNAL_KEYS == set(), receipt["receipt_id"]
        assert set(receipt["surplus"]) == {"buyer"}, receipt["receipt_id"]


def test_internal_audit_keeps_supplier_side_numbers() -> None:
    scenario = load_json(SCENARIO)
    sealed_audit = build_internal_audit(scenario, "sealed")
    unsealed_audit = build_internal_audit(scenario, "unsealed")

    assert sealed_audit["receipt_ref"] == "v0_10x5-sealed-v0.1.0"
    assert sealed_audit["surplus"] == {"buyer": 13430.0, "supplier": 5900.0, "total": 19330.0}
    assert unsealed_audit["surplus"] == {"buyer": 11171.0, "supplier": 7519.0, "total": 18690.0}
    l1 = sealed_audit["assignments"][0]
    assert (l1["lot_id"], l1["supplier_id"], l1["true_unit_cost"], l1["supplier_surplus"]) == ("L1", "S07", 10.4, 1040.0)
    for path in sorted((ROOT / "runs").glob("*/receipt.json")):
        committed = load_json(path.with_name("internal_audit.json"))
        assert committed["receipt_ref"] == load_json(path)["receipt_id"]


def test_validate_receipt_rejects_internal_fields() -> None:
    receipt = build_receipt(load_json(SCENARIO), "sealed")
    leaky = copy.deepcopy(receipt)
    leaky["assignments"][0]["opened_bid"]["true_unit_cost"] = 10.4
    leaky["assignments"][1]["supplier_surplus"] = 1200.0
    leaky["surplus"]["supplier"] = 5900.0

    errors = validate_receipt_data(leaky)
    assert "assignment true_unit_cost belongs in the internal audit, not the receipt" in errors
    assert "assignment supplier_surplus belongs in the internal audit, not the receipt" in errors
    assert "surplus.supplier belongs in the internal audit, not the receipt" in errors


def test_sealed_winners_and_surplus_are_pinned() -> None:
    # Golden-master lock on the sealed clearing. Winner ids depend on the capacity
    # eligibility filter direction; flipping the comparison reshuffles every winner.
    scenario = load_json(SCENARIO)
    sealed = build_receipt(scenario, "sealed")

    winners = [(a["lot_id"], a["supplier_id"]) for a in sealed["assignments"]]
    assert winners == [
        ("L1", "S07"),
        ("L2", "S08"),
        ("L3", "S08"),
        ("L4", "S07"),
        ("L5", "S08"),
    ]
    assert sealed["surplus"]["buyer"] == 13430.0


def test_unsealed_markup_and_surplus_delta_are_pinned() -> None:
    # Golden-master lock on the defensive-markup factor. The unsealed L1 winner S08
    # bids 12.20 with a 0.03 markup, so 12.20 * 1.03 == 12.57. Halving the markup
    # multiplier in runtime_price moves this cleared price and the surplus delta.
    scenario = load_json(SCENARIO)
    sealed = build_receipt(scenario, "sealed")
    unsealed = build_receipt(scenario, "unsealed")

    unsealed_l1 = next(a for a in unsealed["assignments"] if a["lot_id"] == "L1")
    assert unsealed_l1["supplier_id"] == "S08"
    assert unsealed_l1["cleared_unit_price"] == 12.57

    delta_buyer = round(sealed["surplus"]["buyer"] - unsealed["surplus"]["buyer"], 2)
    assert delta_buyer == 2259.00


def test_validate_rejects_out_of_range_markup() -> None:
    scenario = load_json(SCENARIO)
    bad = copy.deepcopy(scenario)
    bad["suppliers"][0]["defensive_markup_pct"] = 5

    errors = validate_scenario_data(bad)
    sid = bad["suppliers"][0]["id"]
    assert f"supplier {sid} defensive_markup_pct must be between 0 and 1" in errors


def test_validate_rejects_single_supplier() -> None:
    scenario = load_json(SCENARIO)
    bad = copy.deepcopy(scenario)
    bad["suppliers"] = bad["suppliers"][:1]

    errors = validate_scenario_data(bad)
    assert "scenario must include at least two suppliers" in errors


def test_surplus_delta_report_is_written() -> None:
    scratch = ROOT / "runs" / "scratch" / "pytest-surplus"
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        sealed_path = write_receipt(SCENARIO, "sealed", scratch / "sealed")
        unsealed_path = write_receipt(SCENARIO, "unsealed", scratch / "unsealed")
        report_path = scratch / "surplus_delta.md"

        write_surplus_report(sealed_path, unsealed_path, report_path)

        report = report_path.read_text(encoding="utf-8")
        assert "Total surplus delta: `640.00`" in report
        assert "| sealed | 13430.00 | 5900.00 | 19330.00 |" in report
        assert "Assignment Comparison" in report
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_cli_validate_missing_path_reports_clean_error(capsys) -> None:
    assert main(["validate", "no_such_file.json"]) == 1

    err = capsys.readouterr().err
    assert "no_such_file.json: file not found" in err


def test_cli_validate_bad_json_reports_clean_error(tmp_path, capsys) -> None:
    garbage = tmp_path / "garbage.json"
    garbage.write_text("{ not json", encoding="utf-8")

    assert main(["validate", str(garbage)]) == 1

    err = capsys.readouterr().err
    assert "invalid JSON" in err
