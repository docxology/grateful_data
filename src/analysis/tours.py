"""Per-tour aggregations."""

from __future__ import annotations

from collections import Counter, defaultdict

from ..integration.reconcile import Compendium


def shows_per_tour(compendium: Compendium) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for s in compendium.shows:
        counter[s.tour or "(untagged)"] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def songs_per_tour(compendium: Compendium) -> dict[str, int]:
    show_to_tour = {s.slug: (s.tour or "(untagged)") for s in compendium.shows}
    per_tour_songs: dict[str, set[str]] = defaultdict(set)
    for p in compendium.performances:
        tour = show_to_tour.get(p.show_slug)
        if tour:
            per_tour_songs[tour].add(p.song_slug)
    return {
        tour: len(songs)
        for tour, songs in sorted(
            per_tour_songs.items(), key=lambda kv: (-len(kv[1]), kv[0])
        )
    }
