#!/usr/bin/env python3
"""Export deterministic sidecar provenance records."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.provenance import write_provenance  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    compendium = load_seed_compendium()
    csv_path, json_path = write_provenance(
        compendium, ROOT / "output" / "data" / "provenance"
    )
    print(f"provenance_csv: {csv_path}")
    print(f"provenance_json: {json_path}")


if __name__ == "__main__":
    main()
