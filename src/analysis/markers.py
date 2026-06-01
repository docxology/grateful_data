"""Canonical set of non-song setlist *segment markers*.

Grateful Dead setlists routinely contain structural segments that are not
compositions: the improvisational ``drums`` / ``space`` core, and generic
``jam`` / ``tuning`` / ``feedback`` interludes. These appear in the performance
table as ``song_slug`` values, but they are not songs in the catalogue sense.

At archival scale they dominate raw performance counts — ``drums`` (1777 rows)
and ``space`` (1247 rows) are the two highest-count slugs in the corpus — so a
naive "most-performed songs" ranking is *true of the data but misleading as
music*. The **repertoire ranking** (``stats.compute`` ``top_songs``) and the
``analysis.repertoire`` module (catalogue coverage, song lifespans, era
turnover) therefore exclude markers by default, surfacing their counts
separately rather than discarding them.

Structural/ordering analyses deliberately **keep** the markers: co-occurrence,
the Markov transition model, and association centrality operate on the full
performance record, because in those contexts a marker adjacency such as
``drums`` → ``space`` is genuine setlist structure, not noise. The raw export,
the performance table, and the category-theoretic *setlist functor* (which
tracks every slug ever performed) likewise keep them. :func:`is_segment_marker`
and :func:`without_segment_markers` are the shared helpers callers use to make
the repertoire-vs-structural distinction explicit.

We deliberately use an explicit curated set rather than a ``*_jam`` rule:
named improvisational pieces such as *Spanish Jam* (``spanish_jam``) and *Mind
Left Body Jam* (``mind_left_body_jam``) are catalogued pieces and must NOT be
swept up as generic markers. Keeping the set explicit makes the exclusion
auditable and conservative.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

#: Generic, non-compositional setlist segment markers (not songs).
SEGMENT_MARKERS: frozenset[str] = frozenset(
    {"drums", "space", "tuning", "jam", "feedback"}
)


def is_segment_marker(slug: str) -> bool:
    """Return ``True`` when ``slug`` is a generic non-song segment marker."""
    return slug in SEGMENT_MARKERS


def without_segment_markers(slugs: Iterable[str]) -> Iterator[str]:
    """Yield ``slugs`` with generic segment markers removed (order preserved)."""
    return (s for s in slugs if s not in SEGMENT_MARKERS)
