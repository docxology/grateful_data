#!/usr/bin/env python3
"""Generate one markdown page per song in the seed."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.reporting.song_pages import write_song_pages  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    print(write_song_pages(load_seed_compendium(), ROOT / "output" / "songs"))


if __name__ == "__main__":
    main()
