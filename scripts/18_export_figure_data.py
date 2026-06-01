#!/usr/bin/env python3
"""Export CSV/JSON datasets backing the registered figure panels."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.seed import load_seed_compendium  # noqa: E402
from src.viz.datasets import export_figure_datasets  # noqa: E402
from src.viz.figures import FIGURE_SPECS  # noqa: E402


def main() -> None:
    comp = load_seed_compendium()
    out_dir = ROOT / "output" / "data" / "figures"
    index_path = export_figure_datasets(comp, FIGURE_SPECS, out_dir)
    print(index_path)


if __name__ == "__main__":
    main()
