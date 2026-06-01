"""Theme-level lyric analytics over the bundled pointer set.

The pointers carry a ``themes`` tuple per song. We aggregate theme frequencies
across the catalog and per-era (a song's era = its first-performance era).
"""

from __future__ import annotations

from collections import Counter

from ..integration.reconcile import Compendium
from .eras import era_of


def theme_frequencies(compendium: Compendium) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for lp in compendium.lyric_pointers:
        for t in lp.themes:
            counter[t] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def themes_by_era(compendium: Compendium) -> dict[str, dict[str, int]]:
    """Theme counts segmented by the era of the song's first performance."""
    songs_by_slug = {s.slug: s for s in compendium.songs}
    by_era: dict[str, Counter[str]] = {}
    for lp in compendium.lyric_pointers:
        song = songs_by_slug.get(lp.song_slug)
        if not song or not song.first_performed:
            continue
        era = era_of(song.first_performed)
        by_era.setdefault(era, Counter())
        for t in lp.themes:
            by_era[era][t] += 1
    return {era: dict(c) for era, c in by_era.items()}


def lyricist_theme_matrix(compendium: Compendium) -> dict[str, dict[str, int]]:
    out: dict[str, Counter[str]] = {}
    for lp in compendium.lyric_pointers:
        out.setdefault(lp.lyricist, Counter())
        for t in lp.themes:
            out[lp.lyricist][t] += 1
    return {lyricist: dict(c) for lyricist, c in out.items()}
