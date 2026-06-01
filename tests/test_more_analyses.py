"""Tests for tours, positions, stationary, centrality, geo, natural transformations, CLI."""

from __future__ import annotations

import io
import json
import sys

import numpy as np
import pytest

from src.analysis import (
    centrality,
    cooccurrence,
    geo,
    positions,
    stationary,
    tours,
    transitions,
)
from src.cattheory.natural import (
    cardinality_eta,
    lineup_cardinality_transformation,
    naturality_square_holds,
    setlist_cardinality_transformation,
)
from src.cli import build_parser, main as cli_main


def test_tours_views(compendium):
    p = tours.shows_per_tour(compendium)
    assert sum(p.values()) == len(compendium.shows)
    songs = tours.songs_per_tour(compendium)
    assert all(v >= 1 for v in songs.values())


def test_positions_views(compendium):
    o = positions.opener_frequency(compendium)
    c = positions.closer_frequency(compendium)
    e = positions.encore_frequency(compendium)
    d = positions.position_distribution(compendium)
    # Total openers across all shows = total set-count.
    n_sets = len({(p.show_slug, p.set_number) for p in compendium.performances})
    assert sum(o.values()) == n_sets
    assert sum(c.values()) == n_sets
    # Position 1 has at least one entry.
    assert d.get(1, 0) >= 1
    # Encore distribution has at least one entry for the bundled multi-set shows.
    assert sum(e.values()) >= 1


def test_stationary_distribution_sums_to_one(compendium):
    tm = transitions.fit(compendium)
    pi = stationary.compute(tm)
    if pi:
        total = sum(pi.values())
        assert abs(total - 1.0) < 1e-6
        for v in pi.values():
            assert v >= 0


def test_stationary_handles_empty():
    from src.analysis.transitions import TransitionModel

    empty = TransitionModel(
        song_slugs=(),
        counts=np.zeros((0, 0), dtype=np.int64),
        transition_matrix=np.zeros((0, 0), dtype=np.float64),
        support=np.zeros((0,), dtype=np.int64),
    )
    assert stationary.compute(empty) == {}


def test_eigenvector_centrality_sums_to_one(compendium):
    songs, m = cooccurrence.cooccurrence_matrix(compendium)
    ec = centrality.eigenvector_centrality(songs, m)
    total = sum(ec.values())
    assert abs(total - 1.0) < 1e-6


def test_eigenvector_centrality_empty():
    assert centrality.eigenvector_centrality((), np.zeros((0, 0))) == {}


def test_geo_loader_and_region_counts(compendium):
    g = geo.load_geo()
    assert len(g) >= 20
    # All show venues have geo coverage in the seed.
    show_venues = {s.venue_slug for s in compendium.shows}
    missing = show_venues - set(g.keys())
    assert not missing, f"missing geo entries: {missing}"
    region_counts = geo.shows_by_region([s.venue_slug for s in compendium.shows], g)
    assert sum(region_counts.values()) == len(compendium.shows)


def test_geo_loader_returns_empty_for_missing_dir(tmp_path):
    assert geo.load_geo(seed_dir=tmp_path) == {}


def test_naturality_square_on_seed(compendium):
    eta = setlist_cardinality_transformation(compendium)
    # Cardinalities are non-decreasing over chronological keys.
    keys = sorted(eta.keys())
    for a, b in zip(keys, keys[1:]):
        assert eta[a] <= eta[b]
    assert naturality_square_holds.__call__  # callable
    from src.cattheory.functors import setlist_functor, lineup_functor

    assert naturality_square_holds(setlist_functor(compendium))
    assert naturality_square_holds(lineup_functor(compendium))
    # And the lineup cardinality is computed.
    lin_eta = lineup_cardinality_transformation(compendium)
    assert max(lin_eta.values()) >= 13


def test_naturality_rejects_broken_inclusion():
    # Hand-constructed broken functor: inclusion fails when |F(d2)| < |F(d1)|.
    broken = {"2001-01-01": frozenset({"a", "b"}), "2002-01-01": frozenset({"a"})}
    assert not naturality_square_holds(broken)


def test_cardinality_eta_pure():
    F = {"2000-01-01": frozenset({"a", "b"}), "2001-01-01": frozenset({"a", "b", "c"})}
    assert cardinality_eta(F) == {"2000-01-01": 2, "2001-01-01": 3}


def _capture_stdout(callable_):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        callable_()
    finally:
        sys.stdout = old
    return buf.getvalue()


def test_cli_stats():
    out = _capture_stdout(lambda: cli_main(["stats"]))
    parsed = json.loads(out)
    assert parsed["n_shows"] >= 80


def test_cli_song_show_person_venue():
    out = _capture_stdout(lambda: cli_main(["song", "ripple"]))
    payload = json.loads(out)
    assert payload["title"] == "Ripple"
    out = _capture_stdout(lambda: cli_main(["show", "1977-05-08@barton_hall_ithaca"]))
    payload = json.loads(out)
    assert payload["date"] == "1977-05-08"
    out = _capture_stdout(lambda: cli_main(["person", "garcia"]))
    payload = json.loads(out)
    assert "Garcia" in payload["full_name"]
    out = _capture_stdout(lambda: cli_main(["venue", "barton_hall_ithaca"]))
    payload = json.loads(out)
    assert payload["city"] == "Ithaca"


def test_cli_list_and_aggregations():
    for kind in ("shows", "songs", "people", "venues", "tours", "releases"):
        out = _capture_stdout(lambda k=kind: cli_main(["list", k]))
        assert out  # non-empty JSON
    out = _capture_stdout(lambda: cli_main(["composers"]))
    parsed = json.loads(out)
    assert "Jerry Garcia" in parsed["songs_by_composer"]
    out = _capture_stdout(lambda: cli_main(["year"]))
    parsed = json.loads(out)
    assert all(isinstance(k, str) and int(k) >= 1969 for k in parsed)


def test_cli_provenance_lookup():
    out = _capture_stdout(lambda: cli_main(["provenance", "songs", "ripple"]))
    parsed = json.loads(out)
    assert parsed[0]["entity_type"] == "songs"
    assert parsed[0]["key"] == "ripple"
    assert parsed[0]["source_keys"]


def test_cli_unknown_targets_raise():
    with pytest.raises(SystemExit):
        cli_main(["song", "no_such_song"])
    with pytest.raises(SystemExit):
        cli_main(["show", "no_such_show"])
    with pytest.raises(SystemExit):
        cli_main(["person", "no_such_person"])
    with pytest.raises(SystemExit):
        cli_main(["venue", "no_such_venue"])


def test_cli_parser_help_works():
    parser = build_parser()
    args = parser.parse_args(["stats"])
    assert args.cmd == "stats"


def test_releases_loaded_into_compendium(compendium):
    assert len(compendium.releases) >= 25
    titles = {r.title for r in compendium.releases}
    assert "Live/Dead" in titles
    assert "American Beauty" in titles
