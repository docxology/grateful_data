"""Performance-as-span construction.

For each ``Performance`` we exhibit a span::

    Show  ←  Performance  →  Song

with the apex projections ``π_show`` and ``π_song``. A *wide pullback* of all
such spans over a fixed show gives that show's setlist (as the limit of all
performance projections into ``Song``). Symmetrically, the wide pullback of
all spans for a fixed song gives that song's performance history (the
multiset of shows in which it appears).

The categorical content is small but real: the performance primitive
*is* the apex linking shows and songs, not a derived field, and the two
projections commute with the cumulative setlist functor by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..integration.reconcile import Compendium
from ..models import Performance


@dataclass(frozen=True)
class PerformanceSpan:
    """A single performance as a span ``Show ← apex → Song``."""

    apex: Performance
    show_slug: str
    song_slug: str

    @classmethod
    def of(cls, p: Performance) -> "PerformanceSpan":
        return cls(apex=p, show_slug=p.show_slug, song_slug=p.song_slug)

    def projection_to_show(self) -> str:
        return self.show_slug

    def projection_to_song(self) -> str:
        return self.song_slug


def build_performance_spans(compendium: Compendium) -> tuple[PerformanceSpan, ...]:
    """One span per performance, ordered canonically."""
    return tuple(
        PerformanceSpan.of(p)
        for p in sorted(
            compendium.performances,
            key=lambda p: (p.show_slug, p.set_number, p.position),
        )
    )


def wide_pullback_over_show(
    spans: tuple[PerformanceSpan, ...], show_slug: str
) -> tuple[str, ...]:
    """The wide pullback of all spans whose left projection is ``show_slug``.

    In our thin setting this is exactly the setlist of that show, in canonical
    order.
    """
    return tuple(s.song_slug for s in spans if s.show_slug == show_slug)


def wide_pullback_over_song(
    spans: tuple[PerformanceSpan, ...], song_slug: str
) -> tuple[str, ...]:
    """The wide pullback of all spans whose right projection is ``song_slug``.

    In our setting this is the song's performance history (show slugs).
    """
    return tuple(s.show_slug for s in spans if s.song_slug == song_slug)


def fibers_over_shows(
    spans: tuple[PerformanceSpan, ...],
) -> dict[str, tuple[str, ...]]:
    """All show-fibers in a single grouping pass (vs O(n) per show).

    Maps each show slug to the ordered tuple of song slugs in its fiber — i.e.
    every show's setlist at once. Equivalent to calling
    :func:`wide_pullback_over_show` for each show, but linear overall, which is
    what makes the commutation check below tractable at archival scale.
    """
    out: dict[str, list[str]] = {}
    for s in spans:
        out.setdefault(s.show_slug, []).append(s.song_slug)
    return {show: tuple(songs) for show, songs in out.items()}


def projections_commute_with_setlist_functor(compendium: Compendium) -> bool:
    """The span projections commute with the cumulative setlist functor.

    For every date ``d``, the union of the show-fibers over all shows on or
    before ``d`` equals the cumulative setlist functor's value ``F(d)``. This
    turns the manuscript's "the two projections commute with the cumulative
    setlist functor by construction" from an assertion into a checked theorem
    over the whole corpus.
    """
    from .functors import setlist_functor

    spans = build_performance_spans(compendium)
    fibers = fibers_over_shows(spans)
    show_date = {s.slug: s.date for s in compendium.shows}
    functor = setlist_functor(compendium)
    # Accumulate fiber songs in date order and compare to F(d) at each date.
    by_date: dict[str, set[str]] = {}
    for show, songs in fibers.items():
        d = show_date.get(show)
        if d is None:
            continue
        by_date.setdefault(d.isoformat(), set()).update(songs)
    cumulative: set[str] = set()
    for d_iso in sorted(by_date):
        cumulative |= by_date[d_iso]
        if frozenset(cumulative) != functor.get(d_iso, frozenset()):
            return False
    return True
