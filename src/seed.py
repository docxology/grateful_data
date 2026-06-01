"""Bundled-seed loader.

Loads the JSON fixtures in ``data/seed/`` into a reconciled ``Compendium``.
The loader is a thin orchestrator over source parsers, schema validation, and
the honesty boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .honesty import HonestyBoundary, HonestyViolation
from .integration.reconcile import Compendium, build_compendium
from .sources.alex_allan import parse as parse_song_record
from .sources.dead_net import parse as parse_person_record
from .sources.internet_archive import parse as parse_recording
from .sources.seed_bundle import (
    parse_citation_record,
    parse_lyric_pointer_record,
    parse_performance_records,
    parse_review_record,
    parse_show_records,
    parse_venue_record,
)
from .sources.wikipedia import parse_release as parse_release_record
from .validation import assert_valid

from .tier import resolve_seed_dir

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


def load_seed_compendium(
    seed_dir: Path | None = None,
    *,
    enforce_honesty: bool = True,
) -> Compendium:
    """Build a ``Compendium`` from bundled fixtures.

    Pass ``seed_dir`` to load from an alternative directory (used by tests).
    """
    base = Path(seed_dir) if seed_dir else resolve_seed_dir()

    def read(name: str) -> list[Any]:
        with (base / name).open("r", encoding="utf-8") as fh:
            data: list[Any] = json.load(fh)
        return data

    raw_payloads = [
        read(name)
        for name in (
            "shows.json",
            "songs.json",
            "personnel.json",
            "venues.json",
            "recordings.json",
            "citations.json",
            "lyric_pointers.json",
            "reviews.json",
        )
    ]

    # Honesty first — forbidden shapes in raw seeds are more specific failures
    # than schema-shape violations, and we want HonestyViolation to win.
    if enforce_honesty:
        boundary = HonestyBoundary()
        raw_violations = boundary.check_payloads(raw_payloads)
        if raw_violations:
            raise HonestyViolation(raw_violations)
    assert_valid(base)

    people = [parse_person_record(r) for r in read("personnel.json")]
    songs = [parse_song_record(r) for r in read("songs.json")]
    venues = [parse_venue_record(v) for v in read("venues.json")]
    shows, perfs = parse_show_records(read("shows.json"))
    perf_path = base / "performances.json"
    if perf_path.exists():
        perfs = parse_performance_records(read("performances.json"))

    recordings = [parse_recording({"metadata": r}) for r in read("recordings.json")]
    try:
        releases_raw = read("releases.json")
    except FileNotFoundError:
        releases_raw = []
    releases = [parse_release_record(r) for r in releases_raw]
    citations = [parse_citation_record(c) for c in read("citations.json")]
    lyric_pointers = [
        parse_lyric_pointer_record(row) for row in read("lyric_pointers.json")
    ]
    reviews = [parse_review_record(row) for row in read("reviews.json")]

    comp = build_compendium(
        shows=shows,
        venues=venues,
        songs=songs,
        people=people,
        performances=perfs,
        recordings=recordings,
        releases=releases,
        citations=citations,
        lyric_pointers=lyric_pointers,
        reviews=reviews,
    )
    if enforce_honesty:
        boundary = HonestyBoundary()
        violations = boundary.check_compendium(comp)
        if violations:
            raise HonestyViolation(violations)
    return comp
