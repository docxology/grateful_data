"""Exploratory repertoire structure over era-by-song performance counts.

This module deliberately stays small and dependency-light: it uses only
``numpy`` plus project primitives. The methods are pattern-discovery aids for
the manuscript and dashboard, not causal, predictive, or definitive
musicological models.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..integration.reconcile import Compendium
from . import distributions, eras
from .markers import is_segment_marker

EXPLORATORY_METHOD_NOTE = (
    "Exploratory pattern-discovery only: fixed preprocessing, centered SVD "
    "coordinates, and deterministic k-means-style clustering over era-by-song "
    "performance counts; no causal or predictive claim is made."
)


@dataclass(frozen=True)
class EraSongMatrix:
    """Era rows by song columns, with raw counts and row-normalized intensity."""

    eras: tuple[str, ...]
    song_slugs: tuple[str, ...]
    counts: np.ndarray
    normalized: np.ndarray
    exclude_segments: bool


@dataclass(frozen=True)
class EmbeddedSong:
    """One song row in the exploratory two-dimensional embedding."""

    song_slug: str
    title: str
    x: float
    y: float
    cluster: int
    n_performances: int
    dominant_era: str
    dominant_era_share: float

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "song_slug": self.song_slug,
            "title": self.title,
            "x": self.x,
            "y": self.y,
            "cluster": self.cluster,
            "n_performances": self.n_performances,
            "dominant_era": self.dominant_era,
            "dominant_era_share": self.dominant_era_share,
        }


@dataclass(frozen=True)
class ClusterSummary:
    """Human-readable summary of one exploratory repertoire cluster."""

    cluster: int
    n_songs: int
    total_performances: int
    dominant_era: str
    top_songs: tuple[tuple[str, int], ...]
    era_counts: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "cluster": self.cluster,
            "n_songs": self.n_songs,
            "total_performances": self.total_performances,
            "dominant_era": self.dominant_era,
            "top_songs": [
                {"song_slug": slug, "n_performances": count}
                for slug, count in self.top_songs
            ],
            "era_counts": [
                {"era": era, "n_performances": count} for era, count in self.era_counts
            ],
        }


@dataclass(frozen=True)
class RepertoireEmbedding:
    """Exploratory SVD embedding plus deterministic cluster summaries."""

    matrix: EraSongMatrix
    songs: tuple[EmbeddedSong, ...]
    clusters: tuple[ClusterSummary, ...]
    component_variance_share: tuple[float, float]
    method_note: str = EXPLORATORY_METHOD_NOTE

    def to_report(self) -> dict[str, object]:
        return {
            "label": "exploratory_repertoire_pattern_discovery",
            "method_note": self.method_note,
            "exclude_segments": self.matrix.exclude_segments,
            "n_songs_embedded": len(self.songs),
            "n_eras": len(self.matrix.eras),
            "n_clusters": len(self.clusters),
            "component_variance_share": {
                "component_1": self.component_variance_share[0],
                "component_2": self.component_variance_share[1],
            },
            "clusters": [cluster.to_dict() for cluster in self.clusters],
            "embedding": [song.to_dict() for song in self.songs],
        }


def _song_title(compendium: Compendium, slug: str) -> str:
    song = compendium.song_by_slug.get(slug)
    if song is not None:
        return song.title
    return slug.replace("_", " ").title()


def era_song_matrix(
    compendium: Compendium,
    *,
    top_n: int = 80,
    exclude_segments: bool = True,
) -> EraSongMatrix:
    """Build an era-by-song matrix for the most-performed repertoire items."""
    ranked = distributions.song_performance_counts(
        compendium, exclude_segments=exclude_segments
    )
    song_slugs = tuple(list(ranked)[:top_n])
    era_names = tuple(name for name, _start, _end in eras.ERAS)
    era_index = {name: idx for idx, name in enumerate(era_names)}
    song_index = {slug: idx for idx, slug in enumerate(song_slugs)}
    counts = np.zeros((len(era_names), len(song_slugs)), dtype=np.int64)
    show_era = {show.slug: eras.era_of(show.date) for show in compendium.shows}
    for perf in compendium.performances:
        if exclude_segments and is_segment_marker(perf.song_slug):
            continue
        col = song_index.get(perf.song_slug)
        row = era_index.get(show_era.get(perf.show_slug, ""))
        if row is None or col is None:
            continue
        counts[row, col] += 1
    totals = counts.sum(axis=1, keepdims=True)
    normalized = np.divide(
        counts.astype(np.float64),
        np.where(totals == 0, 1, totals),
        out=np.zeros_like(counts, dtype=np.float64),
    )
    return EraSongMatrix(
        eras=era_names,
        song_slugs=song_slugs,
        counts=counts,
        normalized=normalized,
        exclude_segments=exclude_segments,
    )


def _centered_svd_coordinates(
    features: np.ndarray,
) -> tuple[np.ndarray, tuple[float, float]]:
    if features.size == 0:
        return np.zeros((features.shape[0], 2), dtype=np.float64), (0.0, 0.0)
    centered = features - features.mean(axis=0, keepdims=True)
    if centered.shape[0] == 0:
        return np.zeros((0, 2), dtype=np.float64), (0.0, 0.0)
    try:
        u, singular, _vh = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError:
        return np.zeros((centered.shape[0], 2), dtype=np.float64), (0.0, 0.0)
    coords = np.zeros((centered.shape[0], 2), dtype=np.float64)
    dims = min(2, u.shape[1], singular.shape[0])
    if dims:
        coords[:, :dims] = u[:, :dims] * singular[:dims]
    variance = singular**2
    total = float(variance.sum())
    shares = [0.0, 0.0]
    if total > 0:
        for idx in range(min(2, len(variance))):
            shares[idx] = round(float(variance[idx] / total), 4)
    return coords, (shares[0], shares[1])


def _initial_centers(coords: np.ndarray, k: int) -> np.ndarray:
    order = sorted(
        range(coords.shape[0]),
        key=lambda idx: (float(coords[idx, 0]), float(coords[idx, 1]), idx),
    )
    if k == 1:
        return coords[[order[len(order) // 2]], :].copy()
    positions = [round(i * (len(order) - 1) / (k - 1)) for i in range(k)]
    chosen: list[int] = []
    for pos in positions:
        idx = order[int(pos)]
        if idx not in chosen:
            chosen.append(idx)
    for idx in order:
        if len(chosen) >= k:
            break
        if idx not in chosen:
            chosen.append(idx)
    return coords[chosen[:k], :].copy()


def _deterministic_kmeans(
    coords: np.ndarray, *, n_clusters: int = 5, max_iter: int = 60
) -> np.ndarray:
    """Small deterministic k-means-style clustering with stable tie-breaks."""
    n = coords.shape[0]
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    k = max(1, min(n_clusters, n))
    centers = _initial_centers(coords, k)
    labels = np.zeros(n, dtype=np.int64)
    for _ in range(max_iter):
        distances = np.sum((coords[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        new_labels = np.argmin(distances, axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for cluster in range(k):
            members = coords[labels == cluster]
            if members.size:
                centers[cluster] = members.mean(axis=0)
            else:
                nearest = np.min(distances, axis=1)
                replacement = max(
                    range(n),
                    key=lambda idx: (float(nearest[idx]), -idx),
                )
                centers[cluster] = coords[replacement]

    order = sorted(
        range(k),
        key=lambda cluster: (
            float(centers[cluster, 0]),
            float(centers[cluster, 1]),
            cluster,
        ),
    )
    remap = {old: new for new, old in enumerate(order)}
    return np.asarray([remap[int(label)] for label in labels], dtype=np.int64)


def _dominant_era(matrix: EraSongMatrix, song_idx: int) -> tuple[str, float]:
    counts = matrix.counts[:, song_idx]
    total = int(counts.sum())
    if total <= 0:
        return "Unknown", 0.0
    idx = max(range(len(matrix.eras)), key=lambda i: (int(counts[i]), -i))
    return matrix.eras[idx], round(float(counts[idx]) / total, 4)


def _cluster_summaries(
    matrix: EraSongMatrix, labels: np.ndarray, *, top_n: int = 5
) -> tuple[ClusterSummary, ...]:
    summaries: list[ClusterSummary] = []
    for cluster in sorted(set(int(label) for label in labels.tolist())):
        member_idxs = [
            idx for idx, label in enumerate(labels.tolist()) if int(label) == cluster
        ]
        song_counts = [
            (matrix.song_slugs[idx], int(matrix.counts[:, idx].sum()))
            for idx in member_idxs
        ]
        song_counts.sort(key=lambda item: (-item[1], item[0]))
        era_counts = [
            (era, int(matrix.counts[era_idx, member_idxs].sum()))
            for era_idx, era in enumerate(matrix.eras)
        ]
        era_counts.sort(key=lambda item: (-item[1], item[0]))
        dominant = era_counts[0][0] if era_counts else "Unknown"
        summaries.append(
            ClusterSummary(
                cluster=cluster,
                n_songs=len(member_idxs),
                total_performances=sum(count for _slug, count in song_counts),
                dominant_era=dominant,
                top_songs=tuple(song_counts[:top_n]),
                era_counts=tuple(era_counts),
            )
        )
    return tuple(summaries)


def repertoire_embedding(
    compendium: Compendium,
    *,
    top_n: int = 80,
    n_clusters: int = 5,
    exclude_segments: bool = True,
) -> RepertoireEmbedding:
    """Compute the deterministic exploratory repertoire embedding."""
    matrix = era_song_matrix(compendium, top_n=top_n, exclude_segments=exclude_segments)
    features = np.log1p(matrix.counts.T.astype(np.float64))
    coords, variance_share = _centered_svd_coordinates(features)
    labels = _deterministic_kmeans(coords, n_clusters=n_clusters)
    songs: list[EmbeddedSong] = []
    for idx, slug in enumerate(matrix.song_slugs):
        dominant_era, dominant_share = _dominant_era(matrix, idx)
        songs.append(
            EmbeddedSong(
                song_slug=slug,
                title=_song_title(compendium, slug),
                x=round(float(coords[idx, 0]), 6),
                y=round(float(coords[idx, 1]), 6),
                cluster=int(labels[idx]),
                n_performances=int(matrix.counts[:, idx].sum()),
                dominant_era=dominant_era,
                dominant_era_share=dominant_share,
            )
        )
    clusters = _cluster_summaries(matrix, labels)
    return RepertoireEmbedding(
        matrix=matrix,
        songs=tuple(songs),
        clusters=clusters,
        component_variance_share=variance_share,
    )


def exploratory_repertoire_report(
    compendium: Compendium,
    *,
    top_n: int = 80,
    n_clusters: int = 5,
) -> dict[str, object]:
    """JSON-serializable report payload for ``analysis_report.json``."""
    return repertoire_embedding(
        compendium, top_n=top_n, n_clusters=n_clusters
    ).to_report()
