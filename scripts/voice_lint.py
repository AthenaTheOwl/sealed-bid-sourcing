from __future__ import annotations

import argparse
import re
from pathlib import Path

TEXT_SUFFIXES = {".md", ".tex", ".bib", ".yaml", ".yml", ".txt"}
BANNED_WORDS = {
    "breakthrough",
    "cutting-edge",
    "disruptive",
    "game-changing",
    "magical",
    "revolutionary",
    "seamless",
    "transformative",
    "unprecedented",
    "world-class",
}
REVERSAL_PATTERNS = [
    re.compile(r"\bnot\s+(?:only|just|merely)\b.{0,120}\bbut\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bnot\b.{0,120}\brather\b", re.IGNORECASE | re.DOTALL),
]


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(candidate for candidate in path.rglob("*") if candidate.suffix in TEXT_SUFFIXES))
        elif path.suffix in TEXT_SUFFIXES:
            files.append(path)
    return files


def lint_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    errors: list[str] = []
    for word in sorted(BANNED_WORDS):
        if word in lower:
            errors.append(f"{path}: marketing word '{word}'")
    for pattern in REVERSAL_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: antithetical-reversal phrasing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    errors: list[str] = []
    for path in iter_files(args.paths):
        errors.extend(lint_file(path))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
