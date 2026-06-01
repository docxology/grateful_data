#!/usr/bin/env python3
"""Emit a single-file HTML dashboard linking every output."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.reporting.dashboard import write_dashboard  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    print(write_dashboard(load_seed_compendium(), ROOT / "output" / "dashboard.html"))


if __name__ == "__main__":
    main()
