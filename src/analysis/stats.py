"""Aggregate descriptive statistics over the compendium."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import islice

from ..integration.reconcile import Compendium
from .markers import SEGMENT_MARKERS, is_segment_marker


@dataclass(frozen=True)
class CompendiumStats:
    """Top-line counts that are easy to verify by hand against the seed."""

    n_shows: int
    n_venues: int
    n_songs: int
    n_people: int
    n_performances: int
    n_recordings: int
    n_releases: int
    n_citations: int
    shows_per_year: dict[int, int]
    top_songs: tuple[tuple[str, int], ...]
    #: Segment-marker performance counts excluded from ``top_songs`` (honesty).
    segment_marker_counts: tuple[tuple[str, int], ...] = ()


def compute(
    compendium: Compendium, top_n: int = 10, *, exclude_segments: bool = True
) -> CompendiumStats:
    """Compute the top-line stats. Deterministic by sorted keys.

    ``top_songs`` ranks *repertoire*: by default generic segment markers
    (``drums``/``space``/``jam``/``tuning``/``feedback``) are excluded because
    they are set segments, not compositions, and otherwise dominate the ranking
    at archival scale. Their counts are surfaced separately in
    ``segment_marker_counts`` so nothing is hidden. Pass
    ``exclude_segments=False`` for the raw, marker-inclusive ranking.
    """
    shows_per_year: Counter[int] = Counter(s.date.year for s in compendium.shows)
    perf_counter: Counter[str] = Counter(p.song_slug for p in compendium.performances)
    segment_marker_counts = tuple(
        (slug, perf_counter[slug])
        for slug in sorted(SEGMENT_MARKERS)
        if slug in perf_counter
    )
    ranked = (
        (slug, n)
        for slug, n in perf_counter.most_common()
        if not (exclude_segments and is_segment_marker(slug))
    )
    top_songs = tuple(islice(ranked, top_n))
    return CompendiumStats(
        n_shows=len(compendium.shows),
        n_venues=len(compendium.venues),
        n_songs=len(compendium.songs),
        n_people=len(compendium.people),
        n_performances=len(compendium.performances),
        n_recordings=len(compendium.recordings),
        n_releases=len(compendium.releases),
        n_citations=len(compendium.citations),
        shows_per_year=dict(sorted(shows_per_year.items())),
        top_songs=top_songs,
        segment_marker_counts=segment_marker_counts,
    )
