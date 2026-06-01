"""Bustout / rotation-gap analytics (compendium-relative).

In Grateful Dead fan vocabulary a song's *gap* is the number of shows since it
was last played; a *bustout* is its return after a long gap. This module
computes gaps over the loaded compendium's chronological show list.

The metric is purely derived from existing ``Performance`` and ``Show`` records
(no new data, no fabrication). It complements ``cooccurrence``/``transitions``
(which see adjacency) with a *recurrence* view (how songs space out over time).

This is a **descriptive** ranking, not an inferential one: ``max_gap_shows`` is
a deterministic function of the data, and the module makes **no claim of
statistical significance, predictiveness, or non-randomness**. A uniformly
played song deterministically yields gap 0 (no false "bustout" signal) — see
``test_song_gaps_negative_control_uniform_play`` for the pinned negative
control that proves the metric does not manufacture structure from uniform
input.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class SongGap:
    """Recurrence summary for one song over the compendium show timeline.

    ``max_gap_shows`` is the largest number of intervening shows between
    two consecutive performances of the song. A song played in every show has
    gap 0; a song with a single performance has gap 0 (no interval to
    measure) and ``n_performances == 1``.

    ``n_performances`` counts the **distinct shows the song was played in**
    (show indices are de-duplicated).
    """

    song_slug: str
    n_performances: int
    max_gap_shows: int


def _ordered_show_slugs(comp: Compendium) -> list[str]:
    """Show slugs in chronological order (date, then slug for ties)."""
    return [s.slug for s in sorted(comp.shows, key=lambda s: (s.date, s.slug))]


def song_gaps(comp: Compendium) -> tuple[SongGap, ...]:
    """Per-song recurrence gaps, sorted by widest gap then slug.

    Performances pointing at a show absent from the compendium are ignored.
    """
    order = _ordered_show_slugs(comp)
    index = {slug: i for i, slug in enumerate(order)}
    plays: dict[str, set[int]] = {}
    for p in comp.performances:
        i = index.get(p.show_slug)
        if i is None:
            continue
        plays.setdefault(p.song_slug, set()).add(i)
    out: list[SongGap] = []
    for slug, idxs in plays.items():
        ordered = sorted(idxs)
        gaps = [b - a - 1 for a, b in zip(ordered, ordered[1:])]
        max_gap = max(gaps) if gaps else 0
        out.append(
            SongGap(song_slug=slug, n_performances=len(ordered), max_gap_shows=max_gap)
        )
    return tuple(sorted(out, key=lambda g: (-g.max_gap_shows, g.song_slug)))


def biggest_bustouts(comp: Compendium, *, top_n: int = 15) -> tuple[SongGap, ...]:
    """Songs with the widest recurrence gap (top returns-after-absence)."""
    return song_gaps(comp)[:top_n]


def rarest_songs(comp: Compendium, *, top_n: int = 15) -> tuple[SongGap, ...]:
    """Songs with the fewest performances (rarities first)."""
    return tuple(
        sorted(song_gaps(comp), key=lambda g: (g.n_performances, g.song_slug))[:top_n]
    )
