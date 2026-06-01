"""Stationary distribution of the song-transition Markov chain.

Computed by power iteration on the row-stochastic transition matrix; we add
an absorbing self-loop on rows with zero out-degree so the matrix remains
stochastic. Convergence is checked against an L1-tolerance.
"""

from __future__ import annotations

import numpy as np

from .transitions import TransitionModel


def compute(
    model: TransitionModel, tol: float = 1e-9, max_iter: int = 2000
) -> dict[str, float]:
    """Return song_slug -> stationary probability."""
    T = model.transition_matrix.copy()
    n = T.shape[0]
    if n == 0:
        return {}
    # Fix zero-row mass on the diagonal so the matrix is stochastic.
    row_sums = T.sum(axis=1)
    for i in range(n):
        if row_sums[i] == 0:
            T[i, i] = 1.0
    pi = np.ones(n) / n
    for _ in range(max_iter):
        nxt = pi @ T
        if np.abs(nxt - pi).sum() < tol:
            pi = nxt
            break
        pi = nxt
    pi = pi / pi.sum()  # final normalize
    return {slug: float(pi[i]) for i, slug in enumerate(model.song_slugs)}
