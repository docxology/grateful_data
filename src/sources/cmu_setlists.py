"""Parser for the Mark Leone CMU setlist archive line format.

The CMU archive at ``cs.cmu.edu/~mleone/gs.html`` (legacy; derivative of Jerry
Stratton's database) stores setlists as plain text. The canonical line shape is::

    1972-08-27 Old Renaissance Faire Grounds, Veneta, OR
    Set 1: Promised Land, Sugaree, Mr. Charlie, ...
    Set 2: China Cat Sunflower-> I Know You Rider, ...
    Encore: One More Saturday Night

We accept that shape verbatim. ``->`` and ``>`` denote segues; we record the
``segue_into`` slug on the predecessor.
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
    normalize_slug,
)

CITATION_KEY = "cmu_leone_setlists"

_HEADER_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<venue>.+?),\s+(?P<city>.+?),\s+(?P<state>[A-Z]{2})\s*$"
)
_SET_RE = re.compile(r"^(?P<label>Set \d+|Encore):\s*(?P<songs>.+)$")


def parse(text: str) -> tuple[Show, Venue, tuple[Performance, ...], tuple[Song, ...]]:
    """Parse one CMU-format show block into schema instances."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("CMU show block is empty")
    header = _HEADER_RE.match(lines[0])
    if not header:
        raise ValueError(f"CMU header malformed: {lines[0]!r}")
    show_date = datetime.strptime(header["date"], "%Y-%m-%d").date()
    venue_name = header["venue"].strip()
    city = header["city"].strip()
    state = header["state"].strip()
    slug = normalize_slug(f"{venue_name}_{city}")
    venue = Venue(slug=slug, name=venue_name, city=city, state_or_region=state)
    show_slug = canonical_show_id(show_date, slug)
    show = Show(slug=show_slug, date=show_date, venue_slug=slug)

    perfs: list[Performance] = []
    songs: dict[str, Song] = {}
    set_counter = 0
    for line in lines[1:]:
        match = _SET_RE.match(line)
        if not match:
            continue
        label = match["label"]
        if label.startswith("Set"):
            set_counter = int(label.split()[1])
        else:  # Encore
            set_counter = max(set_counter, 1) + 1
        tokens = _split_segues(match["songs"])
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


def _split_segues(raw: str) -> list[tuple[str, bool]]:
    """Split a CMU-format set listing, marking segues.

    Songs are separated by ``,`` (no segue) or ``->`` / ``>`` (segue). A
    leftover trailing ``->`` on a comma-separated item also denotes a segue.
    """
    # First split on segue tokens (longest match first), tracking segue
    # positions. We replace ``->`` with a sentinel before splitting on ``>``.
    sentinel = "␟"  # unit separator — won't appear in song titles
    normalized = raw.replace("->", sentinel).replace(">", sentinel)
    # Now split on commas to get top-level items; within each, split on the
    # sentinel to recover segued song pairs.
    items_with_segues: list[tuple[str, bool]] = []
    comma_items = [c for c in normalized.split(",")]
    for ci_idx, comma_item in enumerate(comma_items):
        parts = [p.strip() for p in comma_item.split(sentinel) if p.strip()]
        for pi, title in enumerate(parts):
            is_segue = pi < len(parts) - 1
            items_with_segues.append((title, is_segue))
        # A trailing sentinel in the comma item flips the last item to segue
        if comma_item.rstrip().endswith(sentinel):
            if items_with_segues:
                last_title, _ = items_with_segues[-1]
                items_with_segues[-1] = (last_title, True)
    return items_with_segues


def parse_many(
    texts: Iterable[str],
) -> list[tuple[Show, Venue, tuple[Performance, ...], tuple[Song, ...]]]:
    return [parse(t) for t in texts]
