"""Lightweight schema validator for the bundled seed.

We deliberately avoid an external JSON-Schema dependency: the contract we
need to enforce on the seed is small and totally specified by the
dataclasses in :mod:`src.models`. The validator here checks the
*shape* (types and required keys) of every seed file before loading,
giving a fail-closed gate that complements
:class:`src.honesty.HonestyBoundary`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .tier import resolve_seed_dir

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"

# (name, required_keys, optional_keys) per seed file. Strict: any extra key
# in a record is a violation. Order matters only for readability.
SEED_FILE_CONTRACT: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "shows.json": (("date", "venue_slug", "setlist"), ("tour", "show_index")),
    "songs.json": (
        ("title",),
        ("composers", "lyricists", "first_performed", "last_performed", "aliases"),
    ),
    "personnel.json": (("slug", "full_name", "intervals"), ()),
    "venues.json": (("slug", "name", "city", "state"), ()),
    "recordings.json": (
        ("identifier", "date", "venue", "coverage", "source"),
        ("show_slug",),
    ),
    "releases.json": (("title", "release_date", "kind"), ()),
    "citations.json": (("key", "title", "url", "kind"), ()),
    "lyric_pointers.json": (("song_slug", "lyricist", "source_url"), ("themes",)),
    "reviews.json": (
        ("show_slug", "author", "sentiment", "summary", "source_url", "kind"),
        (),
    ),
    "venue_geo.json": (("venue_slug", "lat", "lon", "region"), ()),
    "performances.json": (
        ("show_slug", "song_slug", "set_number", "position"),
        ("segue_into", "notes"),
    ),
}


def _check_record(
    file: str,
    record: Any,
    required: tuple[str, ...],
    optional: tuple[str, ...],
    idx: int,
) -> list[str]:
    out: list[str] = []
    if not isinstance(record, dict):
        return [f"{file}[{idx}]: not an object"]
    allowed = set(required) | set(optional)
    for r in required:
        if r not in record:
            out.append(f"{file}[{idx}]: missing required {r!r}")
    for k in record:
        if k not in allowed:
            out.append(f"{file}[{idx}]: unexpected key {k!r}")
    return out


def validate_seed(seed_dir: Path | None = None) -> tuple[str, ...]:
    """Return a tuple of human-readable violation strings (empty on pass)."""
    base = Path(seed_dir) if seed_dir else resolve_seed_dir()
    violations: list[str] = []
    for name, (required, optional) in SEED_FILE_CONTRACT.items():
        path = base / name
        if not path.exists():
            if name == "performances.json":
                continue
            violations.append(f"{name}: missing")
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except json.JSONDecodeError as exc:
            violations.append(f"{name}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(payload, list):
            violations.append(f"{name}: top-level must be an array")
            continue
        for i, record in enumerate(payload):
            violations.extend(_check_record(name, record, required, optional, i))
    return tuple(violations)


class SeedValidationError(Exception):
    def __init__(self, violations: tuple[str, ...]) -> None:
        super().__init__("seed validation failed: " + "; ".join(violations))
        self.violations = violations


def assert_valid(seed_dir: Path | None = None) -> None:
    v = validate_seed(seed_dir)
    if v:
        raise SeedValidationError(v)
