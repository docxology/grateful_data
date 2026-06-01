"""Resolve which bundled data tier to load (demonstrator seed vs archival snapshot)."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = PROJECT_ROOT / "data" / "seed"
ARCHIVAL_DIR = PROJECT_ROOT / "data" / "archival"


def resolve_seed_dir(tier: str | None = None) -> Path:
    """Return ``data/seed`` or ``data/archival`` based on tier/env."""
    if tier is None:
        tier = os.environ.get("GRATEFUL_DATA_TIER", "seed").strip().lower()
    if tier == "archival":
        if not ARCHIVAL_DIR.is_dir():
            raise FileNotFoundError(
                f"Archival tier requested but {ARCHIVAL_DIR} is missing; "
                "run scripts/00_fetch_sources.py --online --write-archival first"
            )
        return ARCHIVAL_DIR
    if tier != "seed":
        raise ValueError(
            f"Unknown GRATEFUL_DATA_TIER {tier!r}; use 'seed' or 'archival'"
        )
    return SEED_DIR
