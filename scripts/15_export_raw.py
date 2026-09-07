#!/usr/bin/env python3
"""Export the complete reconciled compendium as raw CSV + JSON.

Thin orchestrator over :func:`src.export.export_all`. Writes every entity to
``output/data/raw/`` as both per-entity CSV and one ``compendium_full.json``.
"""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.export import export_all  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    out_dir = ROOT / "output" / "data" / "raw"
    comp = load_seed_compendium()
    written = export_all(comp, out_dir)
    for name, path in written.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
