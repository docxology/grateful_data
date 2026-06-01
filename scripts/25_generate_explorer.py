#!/usr/bin/env python3
"""Generate a plain static explorer under ``output/explorer/``."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.reporting.explorer import write_explorer  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    compendium = load_seed_compendium()
    html_path, data_path = write_explorer(compendium, ROOT / "output" / "explorer")
    print(f"explorer_html: {html_path}")
    print(f"explorer_data: {data_path}")


if __name__ == "__main__":
    main()
