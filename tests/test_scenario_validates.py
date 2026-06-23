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
