import copy
import json
import shutil
from pathlib import Path

from sealed_bid_sourcing import (
    build_receipt,
    load_json,
    validate_receipt_data,
    validate_scenario_data,
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
    assert sealed["surplus"]["total"] >= unsealed["surplus"]["total"]


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
    scenario = load_json(SCENARIO)
    scratch = ROOT / "runs" / "scratch" / "pytest-surplus"
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        sealed_path = scratch / "sealed.json"
        unsealed_path = scratch / "unsealed.json"
        report_path = scratch / "surplus_delta.md"
        sealed_path.write_text(json.dumps(build_receipt(scenario, "sealed")), encoding="utf-8")
        unsealed_path.write_text(json.dumps(build_receipt(scenario, "unsealed")), encoding="utf-8")

        write_surplus_report(sealed_path, unsealed_path, report_path)

        report = report_path.read_text(encoding="utf-8")
        assert "Total surplus delta" in report
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
