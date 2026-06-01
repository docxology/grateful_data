"""Centrality metrics over the song co-occurrence graph.

We compute eigenvector centrality by power iteration on a symmetric
non-negative adjacency matrix with the diagonal cleared; the dominant
eigenvector (guaranteed non-negative by Perron–Frobenius) is normalized to
sum to one.

Note on interpretation: applied to the **raw co-occurrence count** matrix,
centrality is strongly correlated with raw play frequency (a song played in
700 shows co-occurs with almost everything), so it is *not* a
frequency-independent score in that case. To measure association-driven
importance — songs that bridge many pairs rather than songs merely played a
lot — pass the Jaccard-association adjacency from
``cooccurrence.jaccard_matrix`` instead. This function is agnostic to which
adjacency it is given; the caller chooses the semantics.
"""

from __future__ import annotations

import numpy as np


def eigenvector_centrality(
    song_slugs: tuple[str, ...],
    matrix: np.ndarray,
    tol: float = 1e-9,
    max_iter: int = 2000,
    *,
    strict: bool = False,
) -> dict[str, float]:
    """Eigenvector centrality by power iteration on a non-negative adjacency.

    Power iteration is only guaranteed to converge to *the* dominant eigenvector
    on an irreducible (connected) graph; on a disconnected adjacency the minor
    components are starved toward zero. The result is therefore trustworthy only
    when the power iteration actually converged within ``max_iter``. With
    ``strict=True`` a non-convergence raises ``RuntimeError`` instead of silently
    returning the last (non-eigenvector) iterate; the default keeps the lenient
    behaviour for callers that only need a ranking. Use
    :func:`eigenvector_centrality_converged` to get the convergence flag.
    """
    scores, _converged = eigenvector_centrality_converged(
        song_slugs, matrix, tol=tol, max_iter=max_iter
    )
    if strict and not _converged:
        raise RuntimeError(
            f"eigenvector centrality did not converge within {max_iter} iterations"
        )
    return scores


def eigenvector_centrality_converged(
    song_slugs: tuple[str, ...],
    matrix: np.ndarray,
    tol: float = 1e-9,
    max_iter: int = 2000,
) -> tuple[dict[str, float], bool]:
    """Like :func:`eigenvector_centrality` but also returns a convergence flag."""
    n = matrix.shape[0]
    if n == 0:
        return {}, True
    A = matrix.copy().astype(np.float64)
    np.fill_diagonal(A, 0.0)
    v = np.ones(n) / n
    converged = False
    for _ in range(max_iter):
        nxt = A @ v
        norm = np.linalg.norm(nxt) or 1.0
        nxt = nxt / norm
        if np.abs(nxt - v).sum() < tol:
            v = nxt
            converged = True
            break
        v = nxt
    total = v.sum() or 1.0
    v = v / total
    return {slug: float(v[i]) for i, slug in enumerate(song_slugs)}, converged
