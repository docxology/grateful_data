#!/usr/bin/env python3
"""Write a first-principles claim/evidence ledger for manuscript governance."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis.first_principles import write_review  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    out_dir = ROOT / "output" / "reports"
    json_path, csv_path = write_review(load_seed_compendium(), out_dir)
    print(json_path)
    print(csv_path)


if __name__ == "__main__":
    main()
