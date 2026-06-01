#!/usr/bin/env python3
"""Generate per-era, per-venue, and per-person markdown summary pages."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.reporting.entity_pages import write_entity_pages  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    era_dir, venue_dir, person_dir = write_entity_pages(
        load_seed_compendium(), ROOT / "output"
    )
    print(era_dir)
    print(venue_dir)
    print(person_dir)


if __name__ == "__main__":
    main()
