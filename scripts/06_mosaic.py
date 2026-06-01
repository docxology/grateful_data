#!/usr/bin/env python3
"""Total Mosaic — one composite PNG showing the extent of every dataset."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root(matplotlib_backend=True)

from src.seed import load_seed_compendium  # noqa: E402
from src.viz.compose import save_mosaic  # noqa: E402


def main() -> None:
    print(
        save_mosaic(load_seed_compendium(), ROOT / "output" / "figures" / "mosaic.png")
    )


if __name__ == "__main__":
    main()
