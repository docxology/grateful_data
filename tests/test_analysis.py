"""Tests for analysis modules against the bundled seed compendium."""

from __future__ import annotations

import numpy as np

from src.analysis import cooccurrence, network, stats, timeseries, transitions


def test_stats_top_line_counts_match_seed(compendium):
    s = stats.compute(compendium)
    assert s.n_people >= 13
    assert s.n_songs >= 70
    assert s.n_shows >= 80
    assert s.n_venues >= 20
    assert s.n_recordings >= 5
    assert s.n_citations >= 25
    assert s.n_performances >= s.n_shows  # every show has ≥1 performance
    assert all(y >= 1969 for y in s.shows_per_year)
    assert all(y <= 1995 for y in s.shows_per_year)
    # Top-songs must be a list of (slug, count) descending
    counts = [c for _slug, c in s.top_songs]
    assert counts == sorted(counts, reverse=True)


def test_cooccurrence_symmetry_and_jaccard(compendium):
    songs, m = cooccurrence.cooccurrence_matrix(compendium)
    assert m.shape == (len(songs), len(songs))
    assert np.allclose(m, m.T)
    # Self-occurrence is the per-song show count
    assert (np.diag(m) >= 1).all()
    # Jaccard symmetric, in [0, 1]
    j = cooccurrence.jaccard_index(m, 0, 1)
    assert 0.0 <= j <= 1.0
    # Zero-row Jaccard returns 0 when union is 0
    empty = np.zeros((2, 2), dtype=np.int64)
    assert cooccurrence.jaccard_index(empty, 0, 1) == 0.0


def test_transitions_rows_are_stochastic(compendium):
    model = transitions.fit(compendium)
    assert model.transition_matrix.shape == (
        len(model.song_slugs),
        len(model.song_slugs),
    )
    row_sums = model.transition_matrix.sum(axis=1)
    # Rows are either ~1 (some transitions observed) or 0 (no out-edges)
    for r in row_sums:
        assert abs(r - 1.0) < 1e-9 or r == 0.0
    succ = transitions.top_successors(model, model.song_slugs[0], k=3)
    assert isinstance(succ, list)
    assert transitions.top_successors(model, "no_such_song") == []


def test_timeseries_aggregations(compendium):
    per_year = timeseries.performances_per_year(compendium)
    assert sum(per_year.values()) == sum(1 for _ in compendium.performances)
    life = timeseries.song_lifecycle(compendium, "estimated_prophet")
    assert life is not None and life[0] >= 1977
    assert timeseries.song_lifecycle(compendium, "no_such_song") is None


def test_network_venue_degrees_and_neighbors(compendium):
    degrees = network.venue_degrees(compendium)
    # Only venues with ≥1 show are returned (degrees ⊆ venues).
    venue_slugs = {v.slug for v in compendium.venues}
    assert all(d.venue_slug in venue_slugs for d in degrees)
    assert all(d.n_shows >= 1 for d in degrees)
    neighbors = network.song_neighbors(compendium, "eyes_of_the_world")
    assert isinstance(neighbors, tuple)
    assert "eyes_of_the_world" not in neighbors
    assert network.song_neighbors(compendium, "no_such_song") == ()
