"""Parser for the Alex Allan (whitegum.com) lyric and song finder.

Alex Allan's ``whitegum.com`` indexes all songs ever played by the Grateful
Dead, both originals and covers, with composer/lyricist attribution. We accept
records of the shape::

    {
      "title": "Box of Rain",
      "composers": ["Phil Lesh"],
      "lyricists": ["Robert Hunter"],
      "first_performed": "1972-03-23",
      "last_performed": "1995-07-09",
      "aliases": ["Box of Rain (Phil)"]
    }

We do NOT bundle lyric text — the index is the asset, the words are not.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import Song, canonical_song_id

CITATION_KEY = "whitegum_alex_allan"


def _maybe_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return datetime.strptime(raw, "%Y-%m-%d").date()


def parse(record: dict[str, Any]) -> Song:
    """Parse an Alex Allan song record into a ``Song``."""
    title = record["title"]
    return Song(
        slug=canonical_song_id(title),
        title=title,
        composers=tuple(record.get("composers", ())),
        lyricists=tuple(record.get("lyricists", ())),
        first_performed=_maybe_date(record.get("first_performed")),
        last_performed=_maybe_date(record.get("last_performed")),
        aliases=tuple(record.get("aliases", ())),
    )
