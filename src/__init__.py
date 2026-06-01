"""The Music Never Stopped — Grateful Data Compendium.

A modular, citation-bound Grateful Dead data compendium with category-theoretic
interpretation. See ``AGENTS.md`` for module orientation and ``README.md`` for
the scaling path from seed to full corpus.
"""

from .models import (
    Citation,
    Lineup,
    LyricPointer,
    Performance,
    Person,
    Recording,
    Release,
    Review,
    Show,
    Song,
    Venue,
    canonical_song_id,
    canonical_show_id,
)

__all__ = [
    "Citation",
    "Lineup",
    "LyricPointer",
    "Performance",
    "Person",
    "Recording",
    "Release",
    "Review",
    "Show",
    "Song",
    "Venue",
    "canonical_song_id",
    "canonical_show_id",
]
