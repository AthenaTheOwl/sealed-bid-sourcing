from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sealed_bid_sourcing import load_json, validate_receipt_data, validate_scenario_data


def iter_json(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)
    return files


def validate_json_schema_file(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]
    required = {"$schema", "title", "type", "properties"}
    missing = sorted(required - set(payload))
    if missing:
        return [f"{path}: schema missing {', '.join(missing)}"]
    return []


def validate_payload(path: Path) -> list[str]:
    payload = load_json(path)
    if path.parts and "schemas" in path.parts:
        return validate_json_schema_file(path)
    if "scenario_id" in payload and "lots" in payload and "bids" in payload:
        return [f"{path}: {error}" for error in validate_scenario_data(payload)]
    if "receipt_id" in payload:
        return [f"{path}: {error}" for error in validate_receipt_data(payload)]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    errors: list[str] = []
    for path in iter_json(args.paths):
        if not path.exists():
            errors.append(f"{path}: missing")
            continue
        errors.extend(validate_payload(path))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
