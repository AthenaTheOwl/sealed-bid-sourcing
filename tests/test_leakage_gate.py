import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = ROOT / "paper" / "leakage_bounds.yaml"
SEALED_RECEIPT = ROOT / "runs" / "sealed_v0" / "receipt.json"


def _gate():
    spec = importlib.util.spec_from_file_location("validate_leakage_bound", ROOT / "scripts" / "validate_leakage_bound.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_gate_passes_on_committed_receipts(capsys) -> None:
    gate = _gate()
    assert gate.main([str(BOUNDS), "--runtime", "sealed"]) == 0
    assert "OK (2 sealed receipt(s) checked)" in capsys.readouterr().out
    assert gate.main([str(BOUNDS), "--runtime", "unsealed"]) == 0
    assert "OK (2 unsealed receipt(s) checked)" in capsys.readouterr().out


def test_gate_fails_when_a_receipt_carries_a_true_cost(tmp_path, capsys) -> None:
    # The gate has to open the receipt: the bound file alone says nothing about
    # what the runtime actually wrote.
    receipt = json.loads(SEALED_RECEIPT.read_text(encoding="utf-8"))
    leaky = copy.deepcopy(receipt)
    leaky["assignments"][0]["opened_bid"]["true_unit_cost"] = 10.4
    path = _write(tmp_path / "receipt.json", leaky)

    assert _gate().main([str(BOUNDS), "--runtime", "sealed", "--receipts", str(path)]) == 1
    out = capsys.readouterr().out
    assert "field assignments[].opened_bid.true_unit_cost is not declared" in out


def test_gate_fails_when_a_receipt_carries_supplier_surplus(tmp_path, capsys) -> None:
    receipt = json.loads(SEALED_RECEIPT.read_text(encoding="utf-8"))
    leaky = copy.deepcopy(receipt)
    leaky["surplus"]["supplier"] = 5900.0
    path = _write(tmp_path / "receipt.json", leaky)

    assert _gate().main([str(BOUNDS), "--runtime", "sealed", "--receipts", str(path)]) == 1
    assert "field surplus.supplier is not declared" in capsys.readouterr().out


def test_gate_fails_when_a_field_maps_to_disallowed_leakage(tmp_path, capsys) -> None:
    # Declaring a leaking field does not launder it: a field mapped to a
    # disallowed category fails the gate.
    receipt = json.loads(SEALED_RECEIPT.read_text(encoding="utf-8"))
    leaky = copy.deepcopy(receipt)
    leaky["assignments"][0]["opened_bid"]["true_unit_cost"] = 10.4
    receipt_path = _write(tmp_path / "receipt.json", leaky)
    bounds = BOUNDS.read_text(encoding="utf-8") + (
        '  "assignments[].opened_bid.true_unit_cost": supplier_true_costs_for_winning_bids\n'
    )
    bounds_path = tmp_path / "leakage_bounds.yaml"
    bounds_path.write_text(bounds, encoding="utf-8")

    assert _gate().main([str(bounds_path), "--runtime", "sealed", "--receipts", str(receipt_path)]) == 1
    out = capsys.readouterr().out
    assert "true_unit_cost to supplier_true_costs_for_winning_bids, which is disallowed" in out
    assert "is disallowed leakage (supplier_true_costs_for_winning_bids)" in out


def test_gate_accepts_an_unassigned_lot(tmp_path) -> None:
    receipt = json.loads(SEALED_RECEIPT.read_text(encoding="utf-8"))
    unassigned = copy.deepcopy(receipt)
    unassigned["assignments"][0].update(
        {"supplier_id": None, "cleared_unit_price": None, "opened_bid": None, "score": None, "status": "unassigned"}
    )
    path = _write(tmp_path / "receipt.json", unassigned)

    assert _gate().main([str(BOUNDS), "--runtime", "sealed", "--receipts", str(path)]) == 0
