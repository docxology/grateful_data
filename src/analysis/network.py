"""Network / graph metrics over venues, songs, and people.

Adjacency is computed from the compendium without an external graph library —
keeping the surface small and deterministic.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class VenueDegree:
    venue_slug: str
    n_shows: int
    n_distinct_songs: int


def venue_degrees(compendium: Compendium) -> tuple[VenueDegree, ...]:
    """Per-venue: how many shows happened there and how many distinct songs."""
    shows_at: dict[str, list[str]] = defaultdict(list)
    for s in compendium.shows:
        shows_at[s.venue_slug].append(s.slug)
    songs_at: dict[str, set[str]] = defaultdict(set)
    show_to_venue = {s.slug: s.venue_slug for s in compendium.shows}
    for p in compendium.performances:
        venue = show_to_venue.get(p.show_slug)
        if venue:
            songs_at[venue].add(p.song_slug)
    out: list[VenueDegree] = []
    for venue, shows in sorted(shows_at.items()):
        out.append(
            VenueDegree(
                venue_slug=venue,
                n_shows=len(shows),
                n_distinct_songs=len(songs_at[venue]),
            )
        )
    return tuple(out)


def song_neighbors(compendium: Compendium, song_slug: str) -> tuple[str, ...]:
    """Songs that share a show with ``song_slug`` at least once."""
    show_to_songs: dict[str, set[str]] = defaultdict(set)
    for p in compendium.performances:
        show_to_songs[p.show_slug].add(p.song_slug)
    neighbors: set[str] = set()
    for songs in show_to_songs.values():
        if song_slug in songs:
            neighbors |= songs
    neighbors.discard(song_slug)
    return tuple(sorted(neighbors))
