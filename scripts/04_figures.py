#!/usr/bin/env python3
"""Generate core publication figures from the compendium."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root(matplotlib_backend=True)

from src.seed import load_seed_compendium  # noqa: E402
from src.viz.figures import render_group  # noqa: E402


def main() -> None:
    render_group(load_seed_compendium(), ROOT / "output" / "figures", "core")


if __name__ == "__main__":
    main()
