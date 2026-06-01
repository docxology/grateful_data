"""Exploratory repertoire analysis tests."""

from __future__ import annotations

from src.analysis import exploratory


def test_era_song_matrix_has_expected_shape(compendium):
    matrix = exploratory.era_song_matrix(compendium, top_n=12)
    assert matrix.counts.shape == (len(matrix.eras), len(matrix.song_slugs))
    assert matrix.normalized.shape == matrix.counts.shape
    assert len(matrix.song_slugs) <= 12
    assert matrix.exclude_segments is True


def test_repertoire_embedding_is_deterministic(compendium):
    first = exploratory.repertoire_embedding(compendium, top_n=20, n_clusters=4)
    second = exploratory.repertoire_embedding(compendium, top_n=20, n_clusters=4)
    assert [song.to_dict() for song in first.songs] == [
        song.to_dict() for song in second.songs
    ]
    assert [cluster.to_dict() for cluster in first.clusters] == [
        cluster.to_dict() for cluster in second.clusters
    ]
    assert len(first.clusters) <= 4
    assert first.component_variance_share[0] >= 0


def test_exploratory_report_labels_non_causal_scope(compendium):
    report = exploratory.exploratory_repertoire_report(
        compendium, top_n=15, n_clusters=3
    )
    assert report["label"] == "exploratory_repertoire_pattern_discovery"
    assert "no causal" in str(report["method_note"])
    assert report["n_songs_embedded"] <= 15
    assert report["n_clusters"] <= 3
