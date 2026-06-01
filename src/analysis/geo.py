"""Geo overlay for venues.

We keep ``Venue`` lat/lon out of the schema (it's optional, not every venue
has it) and load it as a sidecar dict ``venue_slug -> {lat, lon, region}``.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from ..tier import resolve_seed_dir

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "seed"


def load_geo(seed_dir: Path | None = None) -> dict[str, dict[str, float | str]]:
    base = Path(seed_dir) if seed_dir else resolve_seed_dir()
    path = base / "venue_geo.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        rows = json.load(fh)
    return {
        r["venue_slug"]: {"lat": r["lat"], "lon": r["lon"], "region": r["region"]}
        for r in rows
    }


def region_counts(
    venue_slugs: Iterable[str], geo: dict[str, dict[str, float | str]]
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for v in venue_slugs:
        info = geo.get(v)
        if info:
            counter[str(info["region"])] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def shows_by_region(
    show_venue_slugs: Iterable[str], geo: dict[str, dict[str, float | str]]
) -> dict[str, int]:
    return region_counts(show_venue_slugs, geo)
