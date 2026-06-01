"""Parser for the gdshowsdb relational dump.

``gdshowsdb`` (Jeff Smith, ``github.com/jefmsmit/gdshowsdb``) ships its data as
a relational schema with tables for ``shows``, ``venues``, ``songs``, and
``performances``. We accept an in-memory representation of the dump as a
``dict`` of lists with the field names taken verbatim from the upstream
README, allowing fresh-clone reconstruction without an SQLite dependency.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import (
    Performance,
    Show,
    Song,
    Venue,
    canonical_show_id,
)

CITATION_KEY = "gdshowsdb"


def _to_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _resolve_show_slug(row: dict[str, Any]) -> str:
    show_date = _to_date(row["date"])
    venue_slug = row["venue_slug"]
    show_index = int(row.get("show_index", 0) or 0)
    expected = canonical_show_id(show_date, venue_slug, show_index=show_index)
    raw = row.get("show_slug")
    return expected if not raw or raw != expected else raw


def parse(
    dump: dict[str, list[dict[str, Any]]],
) -> tuple[
    tuple[Show, ...],
    tuple[Venue, ...],
    tuple[Song, ...],
    tuple[Performance, ...],
]:
    """Parse a ``gdshowsdb`` dict-of-tables dump.

    Expected tables and required columns::

        venues:        venue_slug, name, city, state, country
        songs:         song_slug, title, composers, lyricists
        shows:         show_slug, date, venue_slug, tour
        performances:  show_slug, song_slug, set_number, position
    """
    venues = tuple(
        Venue(
            slug=row["venue_slug"],
            name=row["name"],
            city=row["city"],
            state_or_region=row["state"],
            country=row.get("country", "USA"),
        )
        for row in dump.get("venues", [])
    )
    songs = tuple(
        Song(
            slug=row["song_slug"],
            title=row["title"],
            composers=tuple(row.get("composers", ())),
            lyricists=tuple(row.get("lyricists", ())),
        )
        for row in dump.get("songs", [])
    )
    shows = tuple(
        Show(
            slug=_resolve_show_slug(row),
            date=_to_date(row["date"]),
            venue_slug=row["venue_slug"],
            tour=row.get("tour"),
        )
        for row in dump.get("shows", [])
    )
    perfs = tuple(
        Performance(
            show_slug=row["show_slug"],
            song_slug=row["song_slug"],
            set_number=int(row["set_number"]),
            position=int(row["position"]),
            segue_into=row.get("segue_into"),
        )
        for row in dump.get("performances", [])
    )
    return shows, venues, songs, perfs
