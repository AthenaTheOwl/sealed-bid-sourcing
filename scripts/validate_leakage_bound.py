from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--runtime", default="sealed")
    args = parser.parse_args()

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
    ]
    missing = [token for token in required if token not in text]
    if missing:
        print(f"ERROR: {path}: missing required leakage tokens: {', '.join(missing)}")
        return 1
    if "\n    allowed_leakage:\n      - losing_bid_values" in text:
        print(f"ERROR: {path}: losing_bid_values cannot be listed as allowed leakage")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
