"""Segue-graph analytics.

A segue (`->` or `>` in the source formats) is an explicit musical link
between consecutive songs in a setlist. The segue graph is a directed
multigraph where edge weight is the number of times that segue occurred
across all shows.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class SegueEdge:
    src: str
    dst: str
    count: int


def segue_edges(compendium: Compendium) -> tuple[SegueEdge, ...]:
    """Return segue edges aggregated across the seed."""
    edges: Counter[tuple[str, str]] = Counter()
    for p in compendium.performances:
        if p.segue_into:
            edges[(p.song_slug, p.segue_into)] += 1
    out = [SegueEdge(src=a, dst=b, count=c) for (a, b), c in edges.items()]
    return tuple(sorted(out, key=lambda e: (-e.count, e.src, e.dst)))


def segue_out_degree(compendium: Compendium) -> dict[str, int]:
    """Per-song out-degree in the segue graph."""
    deg: Counter[str] = Counter()
    for e in segue_edges(compendium):
        deg[e.src] += e.count
    return dict(sorted(deg.items(), key=lambda kv: (-kv[1], kv[0])))


def segue_in_degree(compendium: Compendium) -> dict[str, int]:
    """Per-song in-degree in the segue graph."""
    deg: Counter[str] = Counter()
    for e in segue_edges(compendium):
        deg[e.dst] += e.count
    return dict(sorted(deg.items(), key=lambda kv: (-kv[1], kv[0])))
