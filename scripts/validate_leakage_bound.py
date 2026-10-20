from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterator

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT_GLOB = "runs/*/receipt.json"


def iter_leaf_paths(value: Any, prefix: str = "") -> Iterator[tuple[str, Any]]:
    """Yield (path, value) for every leaf of a receipt.

    List items share one path segment (`assignments[].lot_id`), so the path names
    a field, not a position. A null or empty container is yielded as a leaf so a
    field that is present but empty still has to be declared.
    """
    if isinstance(value, dict) and value:
        for key, item in value.items():
            yield from iter_leaf_paths(item, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list) and value:
        for item in value:
            yield from iter_leaf_paths(item, f"{prefix}[]")
    else:
        yield prefix, value


def is_declared(path: str, value: Any, receipt_fields: dict[str, str]) -> bool:
    if path in receipt_fields:
        return True
    # A null or empty container (an unassigned lot's opened_bid, say) leaks nothing
    # beyond its own presence; accept it when its children are declared.
    if value is None or value == {} or value == []:
        return any(field.startswith((f"{path}.", f"{path}[]")) for field in receipt_fields)
    return False


def check_receipt(
    receipt_path: Path,
    runtime: str,
    receipt_fields: dict[str, str],
    allowed: set[str],
    disallowed: set[str],
) -> list[str]:
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{receipt_path}: cannot read receipt ({exc})"]
    if receipt.get("runtime") != runtime:
        return [f"{receipt_path}: receipt is for runtime {receipt.get('runtime')!r}, gate was run for {runtime!r}"]
    errors: list[str] = []
    # Check every leaf, not just the first value seen at each path: an unassigned
    # lot's null opened_bid must not wave through a later lot's leaked value.
    # Dedupe on (path, empty-or-not) to keep the work and the report small.
    seen: set[tuple[str, bool]] = set()
    for path, value in iter_leaf_paths(receipt):
        key = (path, value is None or value == {} or value == [])
        if key in seen:
            continue
        seen.add(key)
        if not is_declared(path, value, receipt_fields):
            errors.append(f"{receipt_path}: field {path} is not declared under receipt_fields")
            continue
        category = receipt_fields.get(path)
        if category is None:
            continue
        if category in disallowed:
            errors.append(f"{receipt_path}: field {path} is disallowed leakage ({category})")
        elif category not in allowed:
            errors.append(f"{receipt_path}: field {path} leaks {category}, which is not in allowed_leakage")
    return list(dict.fromkeys(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--runtime", default="sealed")
    parser.add_argument(
        "--receipts",
        nargs="+",
        help=f"buyer-facing receipts to open (default: every {DEFAULT_RECEIPT_GLOB} for the runtime)",
    )
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path}: missing")
        return 1

    text = path.read_text(encoding="utf-8")
    required = [
        "schema_version:",
        "runtime_profiles:",
        f"  {args.runtime}:",
        "threat_model:",
        "allowed_leakage:",
        "disallowed_leakage:",
        "winner_supplier_ids",
        "opened_winning_bid_values",
        "losing_bid_values",
        "private set intersection",
        "additive secret sharing",
        "receipt_fields:",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        print(f"ERROR: {path}: missing required leakage tokens: {', '.join(missing)}")
        return 1
    if "\n    allowed_leakage:\n      - losing_bid_values" in text:
        print(f"ERROR: {path}: losing_bid_values cannot be listed as allowed leakage")
        return 1

    bounds = yaml.safe_load(text)
    profile = bounds["runtime_profiles"][args.runtime]
    allowed = set(profile.get("allowed_leakage") or [])
    disallowed = set(profile.get("disallowed_leakage") or [])
    receipt_fields = bounds.get("receipt_fields") or {}
    errors: list[str] = []
    for category in sorted(allowed & disallowed):
        errors.append(f"{path}: {category} is listed as both allowed and disallowed for {args.runtime}")
    for field, category in sorted(receipt_fields.items()):
        if category in disallowed:
            errors.append(f"{path}: receipt_fields maps {field} to {category}, which is disallowed for {args.runtime}")

    # The declarations above are only half of the gate. Open the receipts the buyer
    # actually gets and fail on any field the bound file does not allow.
    if args.receipts:
        receipt_paths = [Path(raw) for raw in args.receipts]
    else:
        receipt_paths = []
        for candidate in sorted(ROOT.glob(DEFAULT_RECEIPT_GLOB)):
            try:
                runtime = json.loads(candidate.read_text(encoding="utf-8")).get("runtime")
            except (OSError, json.JSONDecodeError):
                runtime = args.runtime  # let check_receipt report it
            if runtime == args.runtime:
                receipt_paths.append(candidate)
            elif not isinstance(runtime, str) or runtime not in bounds["runtime_profiles"]:
                # A receipt no profile covers would otherwise pass every gate run unread.
                errors.append(
                    f"{candidate}: runtime {runtime!r} has no profile under runtime_profiles; receipt not checked"
                )
    if not receipt_paths:
        errors.append(f"no {args.runtime} receipts found under {DEFAULT_RECEIPT_GLOB}; nothing to check")
    for receipt_path in receipt_paths:
        errors.extend(check_receipt(receipt_path, args.runtime, receipt_fields, allowed, disallowed))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK ({len(receipt_paths)} {args.runtime} receipt(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
