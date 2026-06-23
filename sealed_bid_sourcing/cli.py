from __future__ import annotations

import argparse
from pathlib import Path

from .model import load_json, validate_receipt_data, validate_scenario_data
from .scoring import write_receipt, write_surplus_report

ROOT = Path(__file__).resolve().parents[1]
SEALED_RECEIPT = ROOT / "runs" / "sealed_v0" / "receipt.json"
UNSEALED_RECEIPT = ROOT / "runs" / "unsealed_v0" / "receipt.json"


def lot_comparison(sealed: dict, unsealed: dict) -> list[dict]:
    """Per-lot sealed-vs-unsealed comparison rows, sorted by buyer-surplus gain."""
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
                "total_surplus_delta": round(s["total_surplus"] - u["total_surplus"], 2),
            }
        )
    return sorted(rows, key=lambda r: -r["buyer_surplus_gain"])


def _cmd_show(args: argparse.Namespace) -> int:
    if not SEALED_RECEIPT.exists() or not UNSEALED_RECEIPT.exists():
        print("ERROR: committed receipts not found under runs/. run the sealed/unsealed runtimes first.")
        return 1
    sealed = load_json(SEALED_RECEIPT)
    unsealed = load_json(UNSEALED_RECEIPT)

    buyer_delta = round(sealed["surplus"]["buyer"] - unsealed["surplus"]["buyer"], 2)
    total_delta = round(sealed["surplus"]["total"] - unsealed["surplus"]["total"], 2)
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
            f"{r['lot']:<5}{r['sealed_winner']:<12}{r['sealed_price']:>8.2f}  "
            f"{r['unsealed_winner']:<14}{r['unsealed_price']:>8.2f}  {r['buyer_surplus_gain']:>12,.2f}"
        )
    print()
    top = rows[0]
    print(
        f"headline: sealing bids returns +{buyer_delta:,.2f} buyer surplus vs the unsealed "
        f"markup baseline (total surplus delta +{total_delta:,.2f})."
    )
    print(
        f"          biggest single-lot gain is {top['lot']}: +{top['buyer_surplus_gain']:,.2f} buyer surplus, "
        f"where unsealed defensive markups push the cleared price from "
        f"{top['sealed_price']:.2f} to {top['unsealed_price']:.2f}."
    )
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    failures: list[str] = []
    paths = args.paths or [
        "scenarios/v0_10x5.json",
        "runs/sealed_v0/receipt.json",
        "runs/unsealed_v0/receipt.json",
    ]
    for path_text in paths:
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

    show = subcommands.add_parser("show", help="print the committed sealed-vs-unsealed surplus comparison")
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
    surplus.add_argument("--sealed", required=True)
    surplus.add_argument("--unsealed", required=True)
    surplus.add_argument("--out", required=True)
    surplus.set_defaults(func=_cmd_surplus_delta)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
