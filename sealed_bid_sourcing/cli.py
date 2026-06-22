from __future__ import annotations

import argparse
from pathlib import Path

from .model import load_json, validate_receipt_data, validate_scenario_data
from .scoring import write_receipt, write_surplus_report


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
