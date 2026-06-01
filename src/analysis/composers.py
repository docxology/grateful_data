"""Composer/lyricist attribution analytics."""

from __future__ import annotations

from collections import Counter

from ..integration.reconcile import Compendium


def composer_song_counts(compendium: Compendium) -> dict[str, int]:
    """Per-composer song count (a composer counts once per co-write)."""
    counter: Counter[str] = Counter()
    for s in compendium.songs:
        for c in s.composers:
            counter[c] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def lyricist_song_counts(compendium: Compendium) -> dict[str, int]:
    """Per-lyricist song count."""
    counter: Counter[str] = Counter()
    for s in compendium.songs:
        for ly in s.lyricists:
            counter[ly] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def composer_performance_counts(compendium: Compendium) -> dict[str, int]:
    """Per-composer performance count (weighted by song popularity).

    A co-written song's full performance count is credited to *every* listed
    composer, so this is intentionally **super-additive**: summing the column
    exceeds ``len(compendium.performances)`` whenever any performed song has
    more than one composer. This is a deliberate "credit each writer fully"
    convention, not double-counting by mistake; use
    :func:`composer_song_counts` for a partition-preserving per-song view.
    """
    perf_per_song: Counter[str] = Counter(p.song_slug for p in compendium.performances)
    counter: Counter[str] = Counter()
    for s in compendium.songs:
        for c in s.composers:
            counter[c] += perf_per_song.get(s.slug, 0)
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))
