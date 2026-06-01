"""Song-by-song co-occurrence within shows.

If two songs are played in the same show (regardless of set or position), they
co-occur once. The matrix entry ``M[i, j]`` is the number of shows in which
song ``i`` and song ``j`` both appear; the diagonal is the per-song show
count.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from ..integration.reconcile import Compendium
from .markers import is_segment_marker


def cooccurrence_matrix(
    compendium: Compendium, *, exclude_segments: bool = False
) -> tuple[tuple[str, ...], np.ndarray]:
    """Return (song_slugs, matrix) for the compendium.

    ``song_slugs`` is sorted; ``matrix`` is square, symmetric, integer-valued.
    """
    show_to_songs: dict[str, set[str]] = defaultdict(set)
    for p in compendium.performances:
        if exclude_segments and is_segment_marker(p.song_slug):
            continue
        show_to_songs[p.show_slug].add(p.song_slug)
    songs_played = sorted({s for songs in show_to_songs.values() for s in songs})
    index = {slug: i for i, slug in enumerate(songs_played)}
    n = len(songs_played)
    matrix = np.zeros((n, n), dtype=np.int64)
    for songs in show_to_songs.values():
        idxs = sorted(index[s] for s in songs)
        for a in idxs:
            for b in idxs:
                matrix[a, b] += 1
    return tuple(songs_played), matrix


def jaccard_index(matrix: np.ndarray, i: int, j: int) -> float:
    """Jaccard index for songs ``i`` and ``j`` derived from co-occurrence."""
    inter = matrix[i, j]
    union = matrix[i, i] + matrix[j, j] - inter
    if union == 0:
        return 0.0
    return float(inter) / float(union)


def jaccard_matrix(matrix: np.ndarray) -> np.ndarray:
    """Symmetric Jaccard-association adjacency from a co-occurrence matrix.

    ``A[i, j] = |i ∩ j| / |i ∪ j|`` for ``i != j`` and ``0`` on the diagonal.
    Unlike the raw count matrix (whose row mass scales with how often a song
    was played), this measures *association strength* independent of raw
    frequency — the right input for centrality that is meant to reward songs
    that bridge many pairs rather than songs that were simply played a lot.
    """
    n = matrix.shape[0]
    out = np.zeros((n, n), dtype=np.float64)
    diag = np.diagonal(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            union = diag[i] + diag[j] - matrix[i, j]
            if union > 0:
                val = float(matrix[i, j]) / float(union)
                out[i, j] = val
                out[j, i] = val
    return out
