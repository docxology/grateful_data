"""Noah Gorstein truckin-through-time SQLite (CMU derivative) gap-fill adapter."""

from __future__ import annotations

import sqlite3
import urllib.request
from collections import defaultdict
from datetime import date as _date
from pathlib import Path

from ..models import (
    Performance,
    Show,
    Song,
    Venue,
    canonical_show_id,
    canonical_song_id,
    normalize_slug,
)
from ._vendor_fetch import vendor_path

TRUCKIN_DB_URL = (
    "https://github.com/noahgorstein/truckin-through-time/raw/main/database.db"
)
SOURCE_LABEL = "truckin_through_time_sqlite"


def _venue_slug(name: str, city: str) -> str:
    return normalize_slug(f"{name}_{city}")


def ensure_truckin_db(*, online: bool) -> Path:
    """Return vendor path to ``database.db``, downloading when ``online``."""
    path = vendor_path("truckin", "database.db")
    if path.is_file():
        return path
    if not online:
        raise FileNotFoundError(f"truckin vendor missing: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        TRUCKIN_DB_URL, headers={"User-Agent": "grateful_data-ingest/1.0"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        path.write_bytes(resp.read())
    return path


def parse_truckin_database(
    db_path: Path,
) -> tuple[list[Show], list[Venue], list[Song], list[Performance]]:
    """Parse truckin-through-time SQLite into compendium entity lists."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                c.date AS show_date,
                v.name AS venue_name,
                v.city AS city,
                v.state AS state,
                sl.id AS setlist_id,
                sl.notes AS set_notes,
                s.title AS song_title,
                ss."order" AS position,
                ss.transition AS segue
            FROM concert c
            JOIN venue v ON v.id = c.venue_id
            JOIN setlist sl ON sl.concert_id = c.id
            JOIN setlistsong ss ON ss.setlist_id = sl.id
            JOIN song s ON s.id = ss.song_id
            ORDER BY c.date, sl.id, ss."order"
            """
        ).fetchall()
    finally:
        conn.close()

    shows: dict[str, Show] = {}
    venues: dict[str, Venue] = {}
    songs: dict[str, Song] = {}
    perfs: list[Performance] = []
    by_setlist: dict[int, list[tuple[str, str, bool, int, int]]] = defaultdict(list)

    for row in rows:
        show_date = _date.fromisoformat(str(row["show_date"]))
        venue_name = str(row["venue_name"]).strip()
        city = str(row["city"] or "").strip()
        if not venue_name:
            continue
        state = str(row["state"] or "")
        vslug = _venue_slug(venue_name, city)
        if vslug not in venues:
            venues[vslug] = Venue(
                slug=vslug, name=venue_name, city=city, state_or_region=state
            )
        show_slug = canonical_show_id(show_date, vslug)
        if show_slug not in shows:
            shows[show_slug] = Show(slug=show_slug, date=show_date, venue_slug=vslug)

        title = str(row["song_title"]).strip()
        if not title:
            continue
        song_slug = canonical_song_id(title)
        if not song_slug:
            continue
        if song_slug not in songs:
            songs[song_slug] = Song(slug=song_slug, title=title)

        notes = str(row["set_notes"] or "").lower()
        set_number = 3 if "encore" in notes else 1
        setlist_id = int(row["setlist_id"])
        by_setlist[setlist_id].append(
            (
                show_slug,
                song_slug,
                bool(int(row["segue"])),
                set_number,
                int(row["position"]),
            ),
        )

    for setlist_id in sorted(by_setlist):
        items = by_setlist[setlist_id]
        for idx, (show_slug, song_slug, segue, set_number, position) in enumerate(
            items
        ):
            segue_into = items[idx + 1][1] if segue and idx + 1 < len(items) else None
            perfs.append(
                Performance(
                    show_slug=show_slug,
                    song_slug=song_slug,
                    set_number=set_number,
                    position=position,
                    segue_into=segue_into,
                ),
            )

    return list(shows.values()), list(venues.values()), list(songs.values()), perfs


def fetch_truckin_shows(*, online: bool) -> tuple[list, list, list, list, str]:
    """Download (if needed) and parse truckin-through-time SQLite."""
    db_path = ensure_truckin_db(online=online)
    shows, venues, songs, perfs = parse_truckin_database(db_path)
    return shows, venues, songs, perfs, SOURCE_LABEL
