from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .model import load_json, validate_receipt_data, validate_scenario_data
from .scoring import (
    audit_path_for,
    load_internal_audit,
    load_scenario_for,
    markup_range,
    unassigned_lots,
    write_receipt,
    write_surplus_report,
    zero_markup_control,
)

ROOT = Path(__file__).resolve().parents[1]
SEALED_RECEIPT = ROOT / "runs" / "sealed_v0" / "receipt.json"
UNSEALED_RECEIPT = ROOT / "runs" / "unsealed_v0" / "receipt.json"


class InputError(Exception):
    """A bad input path or payload that should surface as a clean CLI error, not a traceback."""


def _read_json(path: str | Path) -> dict:
    # Convert filesystem and decode failures into a single actionable message so the
    # CLI never dumps a raw traceback for a caller-supplied path.
    try:
        return load_json(path)
    except FileNotFoundError:
        raise InputError(f"{path}: file not found")
    except IsADirectoryError:
        raise InputError(f"{path}: is a directory, expected a JSON file")
    except OSError as exc:
        raise InputError(f"{path}: cannot read ({exc.strerror or exc})")
    except json.JSONDecodeError as exc:
        raise InputError(f"{path}: invalid JSON ({exc})")


def lot_comparison(sealed: dict, unsealed: dict) -> list[dict]:
    """Per-lot sealed-vs-unsealed comparison rows from the receipts, sorted by buyer-surplus gain."""
    sealed_by_lot = {a["lot_id"]: a for a in sealed["assignments"]}
    unsealed_by_lot = {a["lot_id"]: a for a in unsealed["assignments"]}
    rows: list[dict] = []
    for lot_id in sorted(sealed_by_lot):
        s = sealed_by_lot[lot_id]
        u = unsealed_by_lot[lot_id]
        rows.append(
            {
                "lot": lot_id,
                "sealed_winner": s["supplier_id"],
                "sealed_price": s["cleared_unit_price"],
                "unsealed_winner": u["supplier_id"],
                "unsealed_price": u["cleared_unit_price"],
                "buyer_surplus_gain": round(s["buyer_surplus"] - u["buyer_surplus"], 2),
            }
        )
    return sorted(rows, key=lambda r: -r["buyer_surplus_gain"])


def _fmt_price(price: float | None) -> str:
    return "-" if price is None else f"{price:.2f}"


def _cmd_show(args: argparse.Namespace) -> int:
    sealed_path = Path(args.sealed)
    unsealed_path = Path(args.unsealed)
    if not (sealed_path.exists() and unsealed_path.exists()):
        print("ERROR: committed receipts not found under runs/. run the sealed/unsealed runtimes first.")
        return 1
    missing_audits = [str(p) for p in (audit_path_for(sealed_path), audit_path_for(unsealed_path)) if not p.exists()]
    if missing_audits:
        print(
            f"ERROR: internal audit file not found: {', '.join(missing_audits)}. "
            "re-run the sealed/unsealed runtimes to write it next to the receipt."
        )
        return 1
    sealed = _read_json(sealed_path)
    unsealed = _read_json(unsealed_path)
    try:
        sealed_audit = load_internal_audit(sealed_path, sealed)
        unsealed_audit = load_internal_audit(unsealed_path, unsealed)
    except ValueError as exc:
        raise InputError(str(exc))

    buyer_delta = round(sealed["surplus"]["buyer"] - unsealed["surplus"]["buyer"], 2)
    total_delta = round(sealed_audit["surplus"]["total"] - unsealed_audit["surplus"]["total"], 2)
    rows = lot_comparison(sealed, unsealed)

    print(f"scenario: {sealed['scenario_id']}  (auction rule: {sealed['auction_rule']})")
    print(f"sealed vs unsealed runtime, {len(rows)} lots")
    print()
    print("buyer surplus per runtime")
    print(f"  sealed   {sealed['surplus']['buyer']:>10,.2f}")
    print(f"  unsealed {unsealed['surplus']['buyer']:>10,.2f}")
    print()
    header = f"{'lot':<5}{'sealed win':<12}{'price':>8}  {'unsealed win':<14}{'price':>8}  {'buyer gain':>12}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['lot']:<5}{r['sealed_winner'] or 'unassigned':<12}{_fmt_price(r['sealed_price']):>8}  "
            f"{r['unsealed_winner'] or 'unassigned':<14}{_fmt_price(r['unsealed_price']):>8}  "
            f"{r['buyer_surplus_gain']:>12,.2f}"
        )
    print()
    sealed_unassigned = unassigned_lots(sealed)
    unsealed_unassigned = unassigned_lots(unsealed)
    if sealed_unassigned or unsealed_unassigned:
        print(
            f"unassigned lots: sealed {', '.join(sealed_unassigned) or 'none'}; "
            f"unsealed {', '.join(unsealed_unassigned) or 'none'} "
            "(an unassigned lot adds 0 buyer surplus; that gap is infeasibility, not a saving)"
        )
        print()
    top = rows[0]
    print(
        f"headline: under the assumed defensive markups, the sealed run keeps {buyer_delta:+,.2f} buyer surplus "
        f"over the unsealed baseline (total surplus delta {total_delta:+,.2f})."
    )
    print(
        "          a modeled result: the zero-markup control in the surplus-delta report shows "
        "how much of it the markup produces."
    )
    if top["sealed_price"] is None or top["unsealed_price"] is None:
        reason = "where one runtime leaves the lot unassigned."
    else:
        reason = (
            f"where unsealed defensive markups push the cleared price from "
            f"{top['sealed_price']:.2f} to {top['unsealed_price']:.2f}."
        )
    print(f"          biggest single-lot gain is {top['lot']}: +{top['buyer_surplus_gain']:,.2f} buyer surplus, {reason}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    failures: list[str] = []
    paths = args.paths or [
        "scenarios/v0_10x5.json",
        "scenarios/v1_20x10.json",
        "runs/sealed_v0/receipt.json",
        "runs/unsealed_v0/receipt.json",
        "runs/sealed_v1/receipt.json",
        "runs/unsealed_v1/receipt.json",
    ]
    for path_text in paths:
        path = Path(path_text)
        paths = sorted(path.rglob("*.json")) if path.is_dir() else [path]
        for json_path in paths:
            payload = _read_json(json_path)
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
    try:
        out_path = write_receipt(args.scenario, args.runtime, args.out)
    except (FileNotFoundError, IsADirectoryError):
        raise InputError(f"{args.scenario}: file not found")
    except OSError as exc:
        raise InputError(f"{args.scenario}: cannot read ({exc.strerror or exc})")
    except json.JSONDecodeError as exc:
        raise InputError(f"{args.scenario}: invalid JSON ({exc})")
    print(out_path)
    return 0


def _write_surplus_jsonl(
    sealed: dict, unsealed: dict, sealed_audit: dict, unsealed_audit: dict, scenario: dict, path: str | Path
) -> Path:
    delta_buyer = round(sealed["surplus"]["buyer"] - unsealed["surplus"]["buyer"], 2)
    delta_supplier = round(sealed_audit["surplus"]["supplier"] - unsealed_audit["surplus"]["supplier"], 2)
    delta_total = round(sealed_audit["surplus"]["total"] - unsealed_audit["surplus"]["total"], 2)
    sealed_by_lot = {assignment["lot_id"]: assignment for assignment in sealed["assignments"]}
    unsealed_by_lot = {assignment["lot_id"]: assignment for assignment in unsealed["assignments"]}
    sealed_audit_by_lot = {row["lot_id"]: row for row in sealed_audit["assignments"]}
    unsealed_audit_by_lot = {row["lot_id"]: row for row in unsealed_audit["assignments"]}
    low_markup, high_markup = markup_range(scenario)
    control = zero_markup_control(scenario)

    records = [
        {
            "record_type": "runtime_summary",
            "scenario_id": sealed["scenario_id"],
            "runtime": "sealed",
            "receipt_id": sealed["receipt_id"],
            "unassigned_lots": unassigned_lots(sealed),
            "buyer_surplus": sealed["surplus"]["buyer"],
            "supplier_surplus": sealed_audit["surplus"]["supplier"],
            "total_surplus": sealed_audit["surplus"]["total"],
        },
        {
            "record_type": "runtime_summary",
            "scenario_id": unsealed["scenario_id"],
            "runtime": "unsealed",
            "receipt_id": unsealed["receipt_id"],
            "unassigned_lots": unassigned_lots(unsealed),
            "buyer_surplus": unsealed["surplus"]["buyer"],
            "supplier_surplus": unsealed_audit["surplus"]["supplier"],
            "total_surplus": unsealed_audit["surplus"]["total"],
        },
        {
            "record_type": "surplus_delta",
            "scenario_id": sealed["scenario_id"],
            "sealed_receipt_id": sealed["receipt_id"],
            "unsealed_receipt_id": unsealed["receipt_id"],
            "buyer_surplus_delta": delta_buyer,
            "supplier_surplus_delta": delta_supplier,
            "total_surplus_delta": delta_total,
            "defensive_markup_pct_min": low_markup,
            "defensive_markup_pct_max": high_markup,
        },
        {
            "record_type": "zero_markup_control",
            "scenario_id": sealed["scenario_id"],
            "defensive_markup_pct": 0.0,
            "buyer_surplus_delta": control["buyer"],
            "supplier_surplus_delta": control["supplier"],
            "total_surplus_delta": control["total"],
        },
    ]
    for lot_id in sorted(sealed_by_lot):
        s = sealed_by_lot[lot_id]
        u = unsealed_by_lot[lot_id]
        records.append(
            {
                "record_type": "lot_delta",
                "scenario_id": sealed["scenario_id"],
                "lot_id": lot_id,
                "sealed_winner": s["supplier_id"],
                "sealed_price": s["cleared_unit_price"],
                "unsealed_winner": u["supplier_id"],
                "unsealed_price": u["cleared_unit_price"],
                "total_surplus_delta": round(
                    sealed_audit_by_lot[lot_id]["total_surplus"] - unsealed_audit_by_lot[lot_id]["total_surplus"], 2
                ),
            }
        )

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, separators=(",", ":")) for record in records]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _cmd_surplus_delta(args: argparse.Namespace) -> int:
    # write_surplus_report reads both receipts and the internal audit next to each;
    # name the offending file when a read fails.
    sealed = _read_json(args.sealed)
    unsealed = _read_json(args.unsealed)
    _read_json(audit_path_for(args.sealed))
    _read_json(audit_path_for(args.unsealed))
    _read_json(args.scenario)
    try:
        scenario = load_scenario_for(args.scenario, sealed, unsealed)
        out_path = write_surplus_report(args.sealed, args.unsealed, args.out, args.scenario)
        sealed_audit = load_internal_audit(args.sealed, sealed)
        unsealed_audit = load_internal_audit(args.unsealed, unsealed)
    except ValueError as exc:
        raise InputError(str(exc))
    _write_surplus_jsonl(
        sealed, unsealed, sealed_audit, unsealed_audit, scenario, Path(out_path).with_suffix(".jsonl")
    )
    print(out_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sealed_bid_sourcing")
    subcommands = parser.add_subparsers(dest="command", required=True)

    show = subcommands.add_parser("show", help="print the committed sealed-vs-unsealed surplus comparison")
    show.add_argument("--sealed", default=SEALED_RECEIPT)
    show.add_argument("--unsealed", default=UNSEALED_RECEIPT)
    show.set_defaults(func=_cmd_show)

    validate = subcommands.add_parser("validate", help="validate scenarios or receipts")
    validate.add_argument("paths", nargs="*")
    validate.set_defaults(func=_cmd_validate)

    run = subcommands.add_parser("run", help="run a reference runtime")
    run.add_argument("--scenario", required=True)
    run.add_argument("--runtime", choices=["sealed", "unsealed"], required=True)
    run.add_argument("--out", required=True)
    run.set_defaults(func=_cmd_run)

    surplus = subcommands.add_parser("surplus-delta", help="write a surplus delta report")
    surplus.add_argument(
        "--scenario", required=True, help="scenario both receipts came from; used for the zero-markup control"
    )
    surplus.add_argument("--sealed", required=True)
    surplus.add_argument("--unsealed", required=True)
    surplus.add_argument("--out", required=True)
    surplus.set_defaults(func=_cmd_surplus_delta)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
