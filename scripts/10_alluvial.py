#!/usr/bin/env python3
"""Three-column alluvial: composer → song → era."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root(matplotlib_backend=True)

from src.seed import load_seed_compendium  # noqa: E402
from src.viz.alluvial import save_alluvial  # noqa: E402
from src.viz.figures import ALLUVIAL_FILENAME  # noqa: E402


def main() -> None:
    path = save_alluvial(
        load_seed_compendium(), ROOT / "output" / "figures" / ALLUVIAL_FILENAME
    )
    print(path)


if __name__ == "__main__":
    main()
