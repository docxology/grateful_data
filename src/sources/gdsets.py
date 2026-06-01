"""Parser for GDsets.com show + memorabilia records.

GDsets covers the Grateful Dead, JGB, Bob Weir, Brent Mydland, Robert Hunter
and related projects, and is best known for indexing ticket stubs and
stage-pass images. We accept a normalized JSON record::

    {
      "date": "1989-07-07",
      "venue": "JFK Stadium",
      "city": "Philadelphia",
      "state": "PA",
      "project": "Grateful Dead",
      "setlist": [
        {"set": 1, "songs": ["Touch of Grey", "Hell in a Bucket"]},
        {"set": 2, "songs": ["Box of Rain", "Foolish Heart"]}
      ],
      "memorabilia": [
        {"kind": "ticket", "url": "https://gdsets.com/..."},
        {"kind": "stagepass", "url": "https://gdsets.com/..."}
      ]
    }

The memorabilia field is preserved as a tuple of (kind, url) pairs alongside
the schema entities — it's relevant for paratextual/visual analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import (
    Performance,
    Show,
    Song,
    Venue,
    canonical_show_id,
    canonical_song_id,
)

CITATION_KEY = "gdsets_com"


def _venue_slug(name: str, city: str) -> str:
    raw = f"{name}_{city}".lower()
    out = []
    for ch in raw:
        out.append(ch if ch.isalnum() else "_")
    return "_".join(filter(None, "".join(out).split("_")))


def parse(
    record: dict[str, Any],
) -> tuple[
    Show,
    Venue,
    tuple[Performance, ...],
    tuple[Song, ...],
    tuple[tuple[str, str], ...],
]:
    """Parse a GDsets record, returning entities plus a memorabilia tuple."""
    show_date = datetime.strptime(record["date"], "%Y-%m-%d").date()
    venue_name = record["venue"]
    city = record.get("city", "")
    state = record.get("state", "")
    slug = _venue_slug(venue_name, city)
    venue = Venue(slug=slug, name=venue_name, city=city, state_or_region=state)
    show_slug = canonical_show_id(show_date, slug)
    show = Show(slug=show_slug, date=show_date, venue_slug=slug)

    perfs: list[Performance] = []
    songs: dict[str, Song] = {}
    for set_blob in record.get("setlist", []):
        set_num = int(set_blob["set"])
        for pos, title in enumerate(set_blob["songs"], start=1):
            song_slug = canonical_song_id(title)
            songs[song_slug] = Song(slug=song_slug, title=title)
            perfs.append(
                Performance(
                    show_slug=show_slug,
                    song_slug=song_slug,
                    set_number=set_num,
                    position=pos,
                )
            )
    memorabilia = tuple(
        (item["kind"], item["url"]) for item in record.get("memorabilia", [])
    )
    return show, venue, tuple(perfs), tuple(songs.values()), memorabilia
