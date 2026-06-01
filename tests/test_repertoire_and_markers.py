"""Tests for segment-marker handling, Markov rigor, and repertoire dynamics.

No mocks: small explicit Compendium fixtures plus the bundled seed.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from src.analysis import (
    centrality,
    composers,
    cooccurrence,
    positions,
    repertoire,
    reviews,
    stats,
    transitions,
)
from src.analysis.markers import (
    SEGMENT_MARKERS,
    is_segment_marker,
    without_segment_markers,
)
from src.integration.reconcile import Compendium
from src.models import Performance, Show, Song, Venue


def _mini_compendium() -> Compendium:
    """Two shows; 'drums'/'space' segments plus real songs, with set order."""
    shows = (
        Show(slug="1977-05-08@a", date=date(1977, 5, 8), venue_slug="a"),
        Show(slug="1990-03-29@b", date=date(1990, 3, 29), venue_slug="b"),
    )
    venues = (
        Venue(slug="a", name="A", city="X", state_or_region="CA", country="USA"),
        Venue(slug="b", name="B", city="Y", state_or_region="NY", country="USA"),
    )
    songs = (
        Song(slug="scarlet_begonias", title="Scarlet Begonias"),
        Song(slug="fire_on_the_mountain", title="Fire on the Mountain"),
        Song(slug="never_played", title="Never Played"),
    )
    perfs = (
        # Deliberately out of position order to test min-position opener.
        Performance(show_slug="1977-05-08@a", song_slug="fire_on_the_mountain",
                    set_number=1, position=2),
        Performance(show_slug="1977-05-08@a", song_slug="scarlet_begonias",
                    set_number=1, position=1),
        Performance(show_slug="1977-05-08@a", song_slug="drums",
                    set_number=2, position=1),
        Performance(show_slug="1990-03-29@b", song_slug="scarlet_begonias",
                    set_number=1, position=1),
        Performance(show_slug="1990-03-29@b", song_slug="space",
                    set_number=1, position=2),
    )
    return Compendium(
        shows=shows,
        venues=venues,
        songs=songs,
        people=(),
        performances=perfs,
        recordings=(),
        releases=(),
        citations=(),
        lyric_pointers=(),
        reviews=(),
    )


# --- segment markers --------------------------------------------------------

def test_segment_markers_membership_and_filter():
    assert is_segment_marker("drums")
    assert is_segment_marker("space")
    assert not is_segment_marker("scarlet_begonias")
    # Named jams are NOT generic markers.
    assert not is_segment_marker("spanish_jam")
    assert not is_segment_marker("mind_left_body_jam")
    kept = list(without_segment_markers(["drums", "ripple", "space", "jam"]))
    assert kept == ["ripple"]


def test_stats_excludes_segments_by_default_but_surfaces_them():
    comp = _mini_compendium()
    s = stats.compute(comp, top_n=10)
    top_slugs = [slug for slug, _n in s.top_songs]
    assert "drums" not in top_slugs and "space" not in top_slugs
    assert "scarlet_begonias" in top_slugs
    # Markers are surfaced separately, not hidden.
    marker_slugs = {slug for slug, _n in s.segment_marker_counts}
    assert marker_slugs == {"drums", "space"}
    # With exclude_segments=False, markers reappear in the ranking.
    raw = stats.compute(comp, top_n=10, exclude_segments=False)
    assert "drums" in {slug for slug, _n in raw.top_songs}


def test_seed_top_songs_descending_and_marker_free(compendium):
    s = stats.compute(compendium)
    counts = [c for _slug, c in s.top_songs]
    assert counts == sorted(counts, reverse=True)
    assert all(not is_segment_marker(slug) for slug, _c in s.top_songs)


# --- opener correctness (min-position, order-independent) -------------------

def test_opener_uses_min_position_not_iteration_order():
    comp = _mini_compendium()
    openers = positions.opener_frequency(comp)
    # Set 1 of show A opens with scarlet (position 1) despite fire arriving first.
    assert openers.get("scarlet_begonias") == 2  # opens set 1 in both shows
    assert openers.get("fire_on_the_mountain") is None
    # One opener per (show, set_number).
    n_sets = len({(p.show_slug, p.set_number) for p in comp.performances})
    assert sum(openers.values()) == n_sets


# --- Markov support + significance ------------------------------------------

def test_transition_model_carries_support(compendium):
    model = transitions.fit(compendium)
    assert model.support.shape == (len(model.song_slugs),)
    assert (model.support == model.counts.sum(axis=1)).all()


def test_transition_sensitivity_reports_segment_and_era_views(compendium):
    report = transitions.transition_sensitivity_report(
        compendium, support_thresholds=(1, 10)
    )
    assert report["method"].startswith("deterministic descriptive")
    policies = report["segment_marker_policies"]
    assert {row["exclude_segments"] for row in policies} == {False, True}
    assert {row["min_predecessor_support"] for row in policies} == {1, 10}
    assert all("top_edges" in row for row in policies)
    assert len(report["era_models"]) >= 3


def test_top_successors_respects_min_support(compendium):
    model = transitions.fit(compendium)
    # A very high support floor suppresses every successor.
    for slug in model.song_slugs[:5]:
        assert transitions.top_successors(model, slug, min_support=10**9) == []


def test_significant_transitions_deterministic_and_bounded(compendium):
    a = transitions.significant_transitions(
        compendium, n_permutations=40, min_support=3, seed=7
    )
    b = transitions.significant_transitions(
        compendium, n_permutations=40, min_support=3, seed=7
    )
    assert a == b  # deterministic for a fixed seed
    for prev, nxt, obs, _thresh in a:
        assert obs > 0
        assert prev in compendium_song_set(compendium)
        assert nxt in compendium_song_set(compendium)


def compendium_song_set(compendium: Compendium) -> set[str]:
    return {p.song_slug for p in compendium.performances}


# --- association-normalized centrality --------------------------------------

def test_jaccard_matrix_is_symmetric_zero_diagonal(compendium):
    _songs, m = cooccurrence.cooccurrence_matrix(compendium)
    j = cooccurrence.jaccard_matrix(m)
    assert j.shape == m.shape
    assert np.allclose(j, j.T)
    assert np.allclose(np.diagonal(j), 0.0)
    assert (j >= 0).all() and (j <= 1).all()


def test_association_centrality_differs_from_raw_frequency(compendium):
    songs, m = cooccurrence.cooccurrence_matrix(compendium)
    raw_c = centrality.eigenvector_centrality(songs, m)
    assoc_c = centrality.eigenvector_centrality(songs, cooccurrence.jaccard_matrix(m))
    assert abs(sum(assoc_c.values()) - 1.0) < 1e-6
    # The two rankings should not be identical — association removes the pure
    # frequency signal, which is the whole point of the normalization.
    raw_rank = [k for k, _ in sorted(raw_c.items(), key=lambda kv: -kv[1])]
    assoc_rank = [k for k, _ in sorted(assoc_c.items(), key=lambda kv: -kv[1])]
    assert raw_rank != assoc_rank


# --- repertoire dynamics ----------------------------------------------------

def test_catalog_coverage_splits_performed_and_orphans():
    comp = _mini_compendium()
    cov = repertoire.catalog_coverage(comp)
    assert cov.n_catalog == 3
    assert "never_played" in cov.never_performed
    assert cov.n_performed_in_catalog == 2
    # Segment markers (drums/space) are EXCLUDED from the catalogue-coverage
    # computation (consistent with stats/repertoire) and reported separately —
    # they are NOT counted as catalogue orphans.
    assert cov.n_segment_markers_performed == 2
    assert "drums" not in cov.performed_not_in_catalog
    assert "space" not in cov.performed_not_in_catalog
    assert cov.performed_not_in_catalog == ()  # no non-marker orphans here
    assert 0.0 <= cov.coverage_pct <= 100.0


def test_song_lifespans_exclude_segments_and_order_by_debut():
    comp = _mini_compendium()
    spans = repertoire.song_lifespans(comp)
    slugs = [ls.song_slug for ls in spans]
    assert "drums" not in slugs and "space" not in slugs
    scarlet = next(ls for ls in spans if ls.song_slug == "scarlet_begonias")
    assert scarlet.first_year == 1977 and scarlet.last_year == 1990
    assert scarlet.span_years == 13
    assert scarlet.n_performances == 2


def test_repertoire_turnover_seed_in_unit_range(compendium):
    turns = repertoire.repertoire_turnover(compendium)
    for t in turns:
        assert 0.0 <= t.jaccard <= 1.0
        assert abs(t.turnover - (1.0 - t.jaccard)) < 1e-9
        assert t.shared <= min(t.n_songs_a, t.n_songs_b)


def test_repertoire_topn_sensitivity_is_deterministic(compendium):
    report = repertoire.repertoire_topn_sensitivity(
        compendium, top_n_values=(5, 10), exclude_segments=True
    )
    assert report == repertoire.repertoire_topn_sensitivity(
        compendium, top_n_values=(5, 10), exclude_segments=True
    )
    rows = report["rows"]
    assert [row["top_n"] for row in rows] == [5, 10]
    assert rows[0]["performance_share_pct"] <= rows[1]["performance_share_pct"]
    assert all(row["era_coverage"] for row in rows)


# --- reviews + composers documentation behavior -----------------------------

def test_sentiment_by_kind_summary_has_support_and_dispersion(compendium):
    summ = reviews.sentiment_by_kind_summary(compendium)
    assert summ  # seed has reviews
    for _kind, stat in summ.items():
        assert set(stat) == {"n", "mean", "stdev"}
        assert stat["n"] >= 1
        assert stat["stdev"] >= 0.0


def test_composer_performance_counts_super_additive(compendium):
    counts = composers.composer_performance_counts(compendium)
    # Documented convention: co-writes credit every composer fully, so the
    # column can sum beyond the number of performances. Just assert it is a
    # non-empty, non-negative mapping (the convention itself is the contract).
    assert counts and all(v >= 0 for v in counts.values())


def test_segment_markers_constant_is_frozenset():
    assert isinstance(SEGMENT_MARKERS, frozenset)
    assert {"drums", "space", "jam", "tuning", "feedback"} <= SEGMENT_MARKERS
