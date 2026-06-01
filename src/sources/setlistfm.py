"""Parser for Setlist.fm show payloads.

Setlist.fm exposes setlists as JSON via its API and as JSON-LD inside its show
pages (see ``https://www.setlist.fm/setlists/grateful-dead-bd6ad4a.html``). The
two share a shape: ``eventDate``, ``venue.{name, city.name, city.stateCode,
city.country.code}``, ``sets.set[].song[].name``. We accept either shape; the
returned dataclasses are the same.
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
    canonical_song_id,
)

CITATION_KEY = "setlistfm_gd"


def _parse_event_date(raw: str) -> date:
    """Setlist.fm uses ``dd-mm-yyyy``. Tolerate ``yyyy-mm-dd`` too."""
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse Setlist.fm eventDate {raw!r}")


def _venue_slug(name: str, city: str) -> str:
    base = f"{name}_{city}".lower()
    out = []
    for ch in base:
        out.append(ch if ch.isalnum() else "_")
    return "_".join(filter(None, "".join(out).split("_")))


def parse(
    payload: dict[str, Any],
) -> tuple[Show, Venue, tuple[Performance, ...], tuple[Song, ...]]:
    """Parse a Setlist.fm show payload.

    Returns the ``Show``, its ``Venue``, the tuple of ``Performance`` rows,
    and the tuple of ``Song`` rows referenced by the show. Songs returned
    here may be partial (title-only); ``integration.reconcile`` joins with
    other sources for composer attribution.
    """
    event_date = _parse_event_date(payload["eventDate"])
    venue_blob = payload["venue"]
    city_blob = venue_blob.get("city", {})
    venue_name = venue_blob["name"]
    city = city_blob.get("name", "")
    state = city_blob.get("stateCode", "")
    country = city_blob.get("country", {}).get("code", "USA")
    slug = _venue_slug(venue_name, city)
    venue = Venue(
        slug=slug, name=venue_name, city=city, state_or_region=state, country=country
    )
    show_slug = canonical_show_id(event_date, slug)
    show = Show(slug=show_slug, date=event_date, venue_slug=slug)

    perfs: list[Performance] = []
    songs: dict[str, Song] = {}
    sets = payload.get("sets", {}).get("set", [])
    for set_idx, set_blob in enumerate(sets, start=1):
        for pos, song_blob in enumerate(set_blob.get("song", []), start=1):
            title = song_blob["name"]
            song_slug = canonical_song_id(title)
            songs[song_slug] = Song(slug=song_slug, title=title)
            perfs.append(
                Performance(
                    show_slug=show_slug,
                    song_slug=song_slug,
                    set_number=set_idx,
                    position=pos,
                )
            )
    return show, venue, tuple(perfs), tuple(songs.values())
