"""Time-series views over performances."""

from __future__ import annotations

from collections import Counter

from ..integration.reconcile import Compendium


def performances_per_year(compendium: Compendium) -> dict[int, int]:
    """Count performances (not shows) per year."""
    show_year = {s.slug: s.date.year for s in compendium.shows}
    counter: Counter[int] = Counter()
    for p in compendium.performances:
        year = show_year.get(p.show_slug)
        if year is not None:
            counter[year] += 1
    return dict(sorted(counter.items()))


def song_lifecycle(compendium: Compendium, song_slug: str) -> tuple[int, int] | None:
    """Return (first_year, last_year) for a song's performances, or None."""
    show_year = {s.slug: s.date.year for s in compendium.shows}
    years = [
        show_year[p.show_slug]
        for p in compendium.performances
        if p.song_slug == song_slug and p.show_slug in show_year
    ]
    if not years:
        return None
    return (min(years), max(years))
