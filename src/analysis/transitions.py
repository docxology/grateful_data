"""First-order Markov-chain model of song transitions inside a setlist.

We treat each show's performances as a sequence ordered by ``(set_number,
position)``. The transition matrix ``T`` is row-stochastic with
``T[i, j]`` = P(next song = ``j`` | previous song = ``i``).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from ..integration.reconcile import Compendium
from . import eras
from .markers import is_segment_marker


@dataclass(frozen=True)
class TransitionModel:
    song_slugs: tuple[str, ...]
    counts: np.ndarray  # raw transition counts (int)
    transition_matrix: np.ndarray  # row-stochastic (float)
    support: np.ndarray  # per-row total out-transitions (int); == counts.sum(axis=1)


def _show_sequences(
    compendium: Compendium,
    *,
    exclude_segments: bool = False,
    show_slugs: set[str] | None = None,
) -> dict[str, list[str]]:
    show_seqs: dict[str, list[str]] = defaultdict(list)
    for p in sorted(
        compendium.performances, key=lambda p: (p.show_slug, p.set_number, p.position)
    ):
        if show_slugs is not None and p.show_slug not in show_slugs:
            continue
        if exclude_segments and is_segment_marker(p.song_slug):
            continue
        show_seqs[p.show_slug].append(p.song_slug)
    return show_seqs


def _counts_from_sequences(
    sequences: list[list[str]], index: dict[str, int]
) -> np.ndarray:
    n = len(index)
    counts = np.zeros((n, n), dtype=np.int64)
    for seq in sequences:
        for prev_slug, next_slug in zip(seq, seq[1:]):
            counts[index[prev_slug], index[next_slug]] += 1
    return counts


def fit(compendium: Compendium, *, exclude_segments: bool = False) -> TransitionModel:
    """Fit a first-order Markov model over song transitions."""
    show_seqs = _show_sequences(compendium, exclude_segments=exclude_segments)
    songs = sorted({s for seq in show_seqs.values() for s in seq})
    index = {slug: i for i, slug in enumerate(songs)}
    counts = _counts_from_sequences(list(show_seqs.values()), index)
    row_sums = counts.sum(axis=1, keepdims=True)
    safe = np.where(row_sums == 0, 1, row_sums)
    transition_matrix = counts.astype(np.float64) / safe
    return TransitionModel(
        song_slugs=tuple(songs),
        counts=counts,
        transition_matrix=transition_matrix,
        support=counts.sum(axis=1),
    )


def _top_transition_rows(
    model: TransitionModel, *, top_n: int = 5
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i, prev_slug in enumerate(model.song_slugs):
        for j, next_slug in enumerate(model.song_slugs):
            count = int(model.counts[i, j])
            if count <= 0:
                continue
            probability = (
                float(model.transition_matrix[i, j]) if int(model.support[i]) else 0.0
            )
            rows.append(
                {
                    "prev": prev_slug,
                    "next": next_slug,
                    "count": count,
                    "probability": round(probability, 4),
                    "predecessor_support": int(model.support[i]),
                }
            )
    rows.sort(key=lambda row: (-int(row["count"]), str(row["prev"]), str(row["next"])))
    return rows[:top_n]


def transition_sensitivity_report(
    compendium: Compendium,
    *,
    support_thresholds: tuple[int, ...] = (1, 5, 10, 20, 50),
    include_era_models: bool = True,
) -> dict[str, object]:
    """Describe transition-model sensitivity without rerunning permutations.

    The expensive FDR screen remains in :func:`transition_significance_summary`.
    This report is a deterministic, descriptive sensitivity layer: it shows how
    the number of visible predecessor rows and transition cells changes across
    support thresholds, with and without generic segment markers, and optionally
    summarizes era-specific transition models.
    """

    policy_rows: list[dict[str, object]] = []
    for exclude_segments in (False, True):
        model = fit(compendium, exclude_segments=exclude_segments)
        nonzero_edges = int(np.count_nonzero(model.counts))
        total_transitions = int(model.counts.sum())
        for threshold in support_thresholds:
            supported_rows = int(np.count_nonzero(model.support >= threshold))
            supported_edges = 0
            for row_idx in np.where(model.support >= threshold)[0]:
                supported_edges += int(np.count_nonzero(model.counts[row_idx, :]))
            policy_rows.append(
                {
                    "exclude_segments": exclude_segments,
                    "min_predecessor_support": threshold,
                    "n_songs": len(model.song_slugs),
                    "n_observed_transitions": total_transitions,
                    "n_nonzero_edges": nonzero_edges,
                    "n_supported_predecessors": supported_rows,
                    "n_supported_edges": supported_edges,
                    "top_edges": _top_transition_rows(model, top_n=5),
                }
            )

    era_rows: list[dict[str, object]] = []
    if include_era_models:
        shows_by_slug = {show.slug: show for show in compendium.shows}
        for era_name, _start, _end in eras.ERAS:
            era_show_slugs = {
                show.slug
                for show in compendium.shows
                if eras.era_of(show.date) == era_name
            }
            show_seqs = _show_sequences(
                compendium, exclude_segments=True, show_slugs=era_show_slugs
            )
            songs = sorted({song for seq in show_seqs.values() for song in seq})
            if not songs:
                era_rows.append(
                    {
                        "era": era_name,
                        "n_shows": len(era_show_slugs),
                        "n_songs": 0,
                        "n_observed_transitions": 0,
                        "n_nonzero_edges": 0,
                        "top_edges": [],
                    }
                )
                continue
            index = {slug: i for i, slug in enumerate(songs)}
            counts = _counts_from_sequences(list(show_seqs.values()), index)
            support = counts.sum(axis=1, keepdims=True)
            safe = np.where(support == 0, 1, support)
            model = TransitionModel(
                song_slugs=tuple(songs),
                counts=counts,
                transition_matrix=counts.astype(np.float64) / safe,
                support=counts.sum(axis=1),
            )
            era_rows.append(
                {
                    "era": era_name,
                    "n_shows": len(era_show_slugs),
                    "n_songs": len(model.song_slugs),
                    "n_observed_transitions": int(model.counts.sum()),
                    "n_nonzero_edges": int(np.count_nonzero(model.counts)),
                    "top_edges": _top_transition_rows(model, top_n=5),
                    "date_min": min(shows_by_slug[slug].date.isoformat() for slug in era_show_slugs)
                    if era_show_slugs
                    else "",
                    "date_max": max(shows_by_slug[slug].date.isoformat() for slug in era_show_slugs)
                    if era_show_slugs
                    else "",
                }
            )

    return {
        "method": "deterministic descriptive sensitivity; no causal or predictive claim",
        "support_thresholds": list(support_thresholds),
        "segment_marker_policies": policy_rows,
        "era_models": era_rows,
    }


def top_successors(
    model: TransitionModel, song: str, k: int = 3, *, min_support: int = 1
) -> list[tuple[str, float]]:
    """Top-``k`` most-likely successors to ``song``.

    ``min_support`` requires the predecessor row to have at least that many
    observed out-transitions before any successor is reported, so a single
    observed transition (``P = 1.0`` on one example) is not surfaced as a
    confident successor alongside a 500-observation estimate.
    """
    if song not in model.song_slugs:
        return []
    i = model.song_slugs.index(song)
    if int(model.support[i]) < min_support:
        return []
    row = model.transition_matrix[i]
    order = np.argsort(-row)[:k]
    return [(model.song_slugs[j], float(row[j])) for j in order if row[j] > 0]


def significant_transitions(
    compendium: Compendium,
    *,
    min_support: int = 20,
    n_permutations: int = 200,
    fdr_q: float = 0.05,
    seed: int = 0,
) -> list[tuple[str, str, float, float]]:
    """Transitions significant under a within-show label-shuffle null + FDR.

    For each show we hold the *sequence length* fixed and shuffle the song
    labels within the show, refitting the transition counts; this preserves
    each show's setlist size while destroying genuine ordering structure. We
    compute an add-one-smoothed empirical p-value per eligible cell (observed
    count > 0 and predecessor support >= ``min_support``), then control the
    **false-discovery rate** across all eligible cells with the
    Benjamini–Hochberg procedure at level ``fdr_q``. Without this correction,
    thresholding ~10^4 cells at p<=0.05 yields ~5% false positives by
    construction (verified on random-order null data); BH makes the reported set
    a multiplicity-controlled claim.

    Returns ``[(prev_slug, next_slug, observed_count, empirical_p_value), ...]``
    for the FDR-significant transitions, sorted by observed count descending.
    Deterministic for a fixed ``seed``.
    """
    summary = transition_significance_summary(
        compendium,
        min_support=min_support,
        n_permutations=n_permutations,
        fdr_q=fdr_q,
        seed=seed,
    )
    return summary["significant"]


def transition_significance_summary(
    compendium: Compendium,
    *,
    min_support: int = 20,
    n_permutations: int = 200,
    fdr_q: float = 0.05,
    seed: int = 0,
) -> dict:
    """Full significance summary with BOTH uncorrected and FDR-controlled counts.

    Returns a dict with ``n_candidates`` (eligible cells), ``n_uncorrected``
    (cells with p<=fdr_q, NO multiplicity control — reported only for
    transparency), ``n_fdr_significant`` (BH-controlled at ``fdr_q``),
    ``fdr_q``, ``n_permutations``, and ``significant`` (the FDR-significant
    transition tuples). The honest headline is ``n_fdr_significant``.
    """
    show_seqs = _show_sequences(compendium)
    songs = sorted({s for seq in show_seqs.values() for s in seq})
    index = {slug: i for i, slug in enumerate(songs)}
    sequences = list(show_seqs.values())
    observed = _counts_from_sequences(sequences, index)

    rng = np.random.default_rng(seed)
    n = len(songs)
    ge_counts = np.zeros((n, n), dtype=np.int64)
    for _ in range(n_permutations):
        shuffled = [list(rng.permutation(seq)) for seq in sequences]
        null_counts = _counts_from_sequences(shuffled, index)
        ge_counts += (null_counts >= observed).astype(np.int64)
    p = (ge_counts + 1) / (n_permutations + 1)
    support = observed.sum(axis=1)

    # Eligible candidate cells: observed > 0 and predecessor has enough support.
    candidates: list[tuple[float, int, int]] = []
    for i in range(n):
        if int(support[i]) < min_support:
            continue
        for j in range(n):
            if observed[i, j] > 0:
                candidates.append((float(p[i, j]), i, j))
    candidates.sort(key=lambda t: t[0])
    m = len(candidates)
    n_uncorrected = sum(1 for pv, _i, _j in candidates if pv <= fdr_q)

    # Benjamini–Hochberg: largest rank k with p_(k) <= (k/m)*q.
    k_max = 0
    for rank, (pv, _i, _j) in enumerate(candidates, start=1):
        if pv <= (rank / m) * fdr_q:
            k_max = rank
    bh_threshold = candidates[k_max - 1][0] if k_max > 0 else 0.0

    sig = [
        (songs[i], songs[j], float(observed[i, j]), float(pv))
        for pv, i, j in candidates
        if pv <= bh_threshold
    ]
    sig.sort(key=lambda t: (-t[2], t[0], t[1]))
    return {
        "n_candidates": m,
        "n_uncorrected": n_uncorrected,
        "n_fdr_significant": len(sig),
        "fdr_q": fdr_q,
        "n_permutations": n_permutations,
        "significant": sig,
    }
