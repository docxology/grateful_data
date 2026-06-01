"""Parser for The SetList Program (setlists.net) export records.

The SetList Program (Hunter Seidman's site, ``setlists.net``) covers 1965-1995.
The site exposes per-show pages plus a downloadable text export with the shape::

    DATE: 1977-05-08
    VENUE: Barton Hall
    CITY: Ithaca
    STATE: NY
    SET 1: Minglewood Blues; Loser; El Paso; They Love Each Other; ...
    SET 2: Scarlet Begonias > Fire on the Mountain; ...
    ENCORE: One More Saturday Night

We accept that record shape verbatim. ``>`` denotes segues.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable

from ..models import (
    Performance,
    Show,
    Song,
    Venue,
    canonical_show_id,
    canonical_song_id,
)

CITATION_KEY = "setlists_net_program"

_FIELD_RE = re.compile(r"^(?P<key>[A-Z][A-Z0-9 ]*?):\s*(?P<value>.+)$")


def _venue_slug(name: str, city: str) -> str:
    raw = f"{name}_{city}".lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_")


def _split_set(raw: str) -> list[tuple[str, bool]]:
    """Split a SetList Program set listing on ``;`` (group) and ``>`` (segue)."""
    out: list[tuple[str, bool]] = []
    for group in (g for g in raw.split(";") if g.strip()):
        segments = [s.strip() for s in group.split(">") if s.strip()]
        for i, title in enumerate(segments):
            is_segue = i < len(segments) - 1
            out.append((title, is_segue))
    return out


def parse(text: str) -> tuple[Show, Venue, tuple[Performance, ...], tuple[Song, ...]]:
    """Parse one SetList Program record block into schema instances."""
    fields: dict[str, str] = {}
    sets: list[tuple[str, list[tuple[str, bool]]]] = []
    for line in (ln.strip() for ln in text.splitlines() if ln.strip()):
        m = _FIELD_RE.match(line)
        if not m:
            continue
        key = m["key"].strip()
        value = m["value"].strip()
        if key.startswith("SET ") or key == "ENCORE":
            sets.append((key, _split_set(value)))
        else:
            fields[key] = value
    if "DATE" not in fields or "VENUE" not in fields:
        raise ValueError("SetList Program record missing DATE or VENUE")
    show_date = datetime.strptime(fields["DATE"], "%Y-%m-%d").date()
    venue_name = fields["VENUE"]
    city = fields.get("CITY", "")
    state = fields.get("STATE", "")
    slug = _venue_slug(venue_name, city)
    venue = Venue(slug=slug, name=venue_name, city=city, state_or_region=state)
    show_slug = canonical_show_id(show_date, slug)
    show = Show(slug=show_slug, date=show_date, venue_slug=slug)

    perfs: list[Performance] = []
    songs: dict[str, Song] = {}
    set_counter = 0
    for label, tokens in sets:
        if label.startswith("SET "):
            set_counter = int(label.split()[1])
        else:
            set_counter = max(set_counter, 1) + 1
        for pos, (title, segue) in enumerate(tokens, start=1):
            song_slug = canonical_song_id(title)
            songs[song_slug] = Song(slug=song_slug, title=title)
            next_slug = (
                canonical_song_id(tokens[pos][0])
                if segue and pos < len(tokens)
                else None
            )
            perfs.append(
                Performance(
                    show_slug=show_slug,
                    song_slug=song_slug,
                    set_number=set_counter,
                    position=pos,
                    segue_into=next_slug,
                )
            )
    return show, venue, tuple(perfs), tuple(songs.values())


def parse_many(
    texts: Iterable[str],
) -> list[tuple[Show, Venue, tuple[Performance, ...], tuple[Song, ...]]]:
    return [parse(t) for t in texts]
