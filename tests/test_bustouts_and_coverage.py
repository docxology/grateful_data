"""Tests for the new bustout/recurrence-gap analysis plus coverage closure
for the segue degree views and the opposite-category closures.

No mocks: every test runs on the real bundled seed (``compendium`` fixture)
or on small hand-built real instances.
"""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.analysis import bustouts, segues
from src.cattheory import opposite
from src.cattheory.categories import build_show_category
from src.viz import panels


# ---------------------------------------------------------------------------
# bustouts (new analysis module)
# ---------------------------------------------------------------------------


def test_song_gaps_cover_all_performed_songs(compendium):
    gaps = bustouts.song_gaps(compendium)
    # Every song that appears in a seed performance gets exactly one SongGap.
    performed = {p.song_slug for p in compendium.performances if p.show_slug}
    seed_show_slugs = {s.slug for s in compendium.shows}
    performed_in_seed = {
        p.song_slug for p in compendium.performances if p.show_slug in seed_show_slugs
    }
    assert {g.song_slug for g in gaps} == performed_in_seed
    assert performed_in_seed <= performed


def test_song_gaps_counts_match_performance_totals(compendium):
    """ISC-16 honesty cross-check: n_performances is the real seed count,
    not a fabricated value."""
    gaps = {g.song_slug: g for g in bustouts.song_gaps(compendium)}
    seed_show_slugs = {s.slug for s in compendium.shows}
    for slug, g in gaps.items():
        actual = sum(
            1
            for p in compendium.performances
            if p.song_slug == slug and p.show_slug in seed_show_slugs
        )
        assert g.n_performances == actual
        assert g.max_gap_shows >= 0
        # A gap can never exceed (total seed shows - 1).
        assert g.max_gap_shows <= len(seed_show_slugs) - 1


def test_song_gaps_sorted_widest_first(compendium):
    gaps = bustouts.song_gaps(compendium)
    widths = [g.max_gap_shows for g in gaps]
    assert widths == sorted(widths, reverse=True)


def test_biggest_bustouts_respects_top_n(compendium):
    top = bustouts.biggest_bustouts(compendium, top_n=5)
    assert len(top) <= 5
    full = bustouts.song_gaps(compendium)
    assert list(top) == list(full[:5])


def test_rarest_songs_orders_by_fewest_performances(compendium):
    rare = bustouts.rarest_songs(compendium, top_n=8)
    counts = [g.n_performances for g in rare]
    assert counts == sorted(counts)
    assert all(g.n_performances >= 1 for g in rare)


def test_song_gaps_single_performance_has_zero_gap():
    """A song played once has no interval, hence gap 0 — built on real
    dataclass instances (no mocks)."""
    from datetime import date

    from src.integration.reconcile import build_compendium
    from src.models import Performance, Show, Venue, canonical_show_id

    venue = Venue(slug="v", name="V", city="C", state_or_region="CA")
    shows = [
        Show(
            slug=canonical_show_id(date(1977, 5, d), "v"),
            date=date(1977, 5, d),
            venue_slug="v",
        )
        for d in (1, 2, 3)
    ]
    perfs = [
        Performance(
            show_slug=shows[0].slug, song_slug="once", set_number=1, position=1
        ),
        Performance(
            show_slug=shows[0].slug, song_slug="every", set_number=1, position=2
        ),
        Performance(
            show_slug=shows[1].slug, song_slug="every", set_number=1, position=1
        ),
        Performance(
            show_slug=shows[2].slug, song_slug="every", set_number=1, position=1
        ),
    ]
    comp = build_compendium(shows=shows, venues=[venue], performances=perfs)
    by_slug = {g.song_slug: g for g in bustouts.song_gaps(comp)}
    assert by_slug["once"].n_performances == 1
    assert by_slug["once"].max_gap_shows == 0
    # "every" played show 0,1,2 → no intervening gap.
    assert by_slug["every"].max_gap_shows == 0


def test_song_gaps_measures_intervening_shows():
    from datetime import date

    from src.integration.reconcile import build_compendium
    from src.models import Performance, Show, Venue, canonical_show_id

    venue = Venue(slug="v", name="V", city="C", state_or_region="CA")
    shows = [
        Show(
            slug=canonical_show_id(date(1977, 5, d), "v"),
            date=date(1977, 5, d),
            venue_slug="v",
        )
        for d in (1, 2, 3, 4)
    ]
    # "rare" played at show 0 and show 3 → 2 intervening shows (1 and 2).
    perfs = [
        Performance(
            show_slug=shows[0].slug, song_slug="rare", set_number=1, position=1
        ),
        Performance(
            show_slug=shows[3].slug, song_slug="rare", set_number=1, position=1
        ),
    ]
    comp = build_compendium(shows=shows, venues=[venue], performances=perfs)
    g = next(x for x in bustouts.song_gaps(comp) if x.song_slug == "rare")
    assert g.max_gap_shows == 2
    assert g.n_performances == 2


def test_song_gaps_negative_control_uniform_play():
    """Negative control: a song played in EVERY consecutive show yields gap 0 —
    the metric does not manufacture a 'bustout' signal from uniform input,
    while a clustered song in the same data shows a real gap. This binds the
    finding (descriptive-only, no fabricated structure), per advisor review."""
    from datetime import date

    from src.integration.reconcile import build_compendium
    from src.models import Performance, Show, Venue, canonical_show_id

    venue = Venue(slug="v", name="V", city="C", state_or_region="CA")
    shows = [
        Show(
            slug=canonical_show_id(date(1977, 5, d), "v"),
            date=date(1977, 5, d),
            venue_slug="v",
        )
        for d in range(1, 6)  # 5 consecutive shows
    ]
    perfs = [
        # "uniform" appears in all 5 shows → no intervening gap anywhere.
        *[
            Performance(show_slug=s.slug, song_slug="uniform", set_number=1, position=1)
            for s in shows
        ],
        # "clustered" appears only at the first and last → real gap of 3.
        Performance(
            show_slug=shows[0].slug, song_slug="clustered", set_number=1, position=2
        ),
        Performance(
            show_slug=shows[4].slug, song_slug="clustered", set_number=1, position=2
        ),
    ]
    comp = build_compendium(shows=shows, venues=[venue], performances=perfs)
    by_slug = {g.song_slug: g for g in bustouts.song_gaps(comp)}
    assert by_slug["uniform"].max_gap_shows == 0  # no false signal
    assert by_slug["clustered"].max_gap_shows == 3  # real recurrence gap surfaced
    # Descriptive determinism: rerunning yields identical results.
    assert bustouts.song_gaps(comp) == bustouts.song_gaps(comp)


def test_song_gaps_ignores_performances_outside_seed():
    from datetime import date

    from src.integration.reconcile import build_compendium
    from src.models import Performance, Show, Venue, canonical_show_id

    venue = Venue(slug="v", name="V", city="C", state_or_region="CA")
    show = Show(
        slug=canonical_show_id(date(1977, 5, 1), "v"),
        date=date(1977, 5, 1),
        venue_slug="v",
    )
    perfs = [
        Performance(show_slug=show.slug, song_slug="real", set_number=1, position=1),
        Performance(
            show_slug="1900-01-01@ghost", song_slug="orphan", set_number=1, position=1
        ),
    ]
    comp = build_compendium(shows=[show], venues=[venue], performances=perfs)
    slugs = {g.song_slug for g in bustouts.song_gaps(comp)}
    assert "real" in slugs
    assert "orphan" not in slugs


# ---------------------------------------------------------------------------
# bustouts panel (figure)
# ---------------------------------------------------------------------------


def test_draw_bustouts_panel(tmp_path, compendium):
    fig, ax = plt.subplots(figsize=(6, 4))
    drawn = panels.draw_bustouts(ax, compendium)
    path = panels.save_figure(fig, tmp_path / "bustouts.png")
    assert path.stat().st_size > 0
    assert isinstance(drawn, bool)


def test_draw_bustouts_empty_state():
    from src.integration.reconcile import build_compendium

    fig, ax = plt.subplots(figsize=(4, 3))
    assert panels.draw_bustouts(ax, build_compendium()) is True
    plt.close(fig)


def test_empty_compendium_draws_honest_empty_states():
    """Data-guarded panels render an honest empty-state instead of raising."""
    from src.integration.reconcile import build_compendium

    empty = build_compendium()
    guarded = [
        panels.draw_era_density,
        panels.draw_lineup_diversity,
        panels.draw_set_positions,
        panels.draw_stationary_top,
        panels.draw_centrality_top,
        panels.draw_releases_timeline,
        panels.draw_tours_top,
        panels.draw_recording_sources_pie,
        panels.draw_lyric_themes,
        panels.draw_personnel_gantt,
        panels.draw_bustouts,
    ]
    for fn in guarded:
        fig, ax = plt.subplots(figsize=(3, 2))
        assert fn(ax, empty) is True, (
            f"{fn.__name__} should render empty-state on empty data"
        )
        plt.close(fig)


def test_draw_geo_scatter_empty_without_geo():
    from src.integration.reconcile import build_compendium

    fig, ax = plt.subplots(figsize=(3, 2))
    assert panels.draw_geo_scatter(ax, build_compendium(), geo_map={}) is True
    plt.close(fig)


def test_draw_segue_graph_with_real_segue_data(tmp_path):
    """The bundled seed has no segue_into edges, so the seed leaves the segue
    panel body unexercised. Drive it with a real built compendium that does."""
    from datetime import date

    from src.integration.reconcile import build_compendium
    from src.models import Performance, Show, Venue, canonical_show_id

    venue = Venue(slug="v", name="V", city="C", state_or_region="CA")
    show = Show(
        slug=canonical_show_id(date(1977, 5, 8), "v"),
        date=date(1977, 5, 8),
        venue_slug="v",
    )
    perfs = [
        Performance(
            show_slug=show.slug,
            song_slug="scarlet",
            set_number=2,
            position=1,
            segue_into="fire",
        ),
        Performance(
            show_slug=show.slug,
            song_slug="fire",
            set_number=2,
            position=2,
            segue_into="estimated",
        ),
        Performance(
            show_slug=show.slug, song_slug="estimated", set_number=2, position=3
        ),
    ]
    comp = build_compendium(shows=[show], venues=[venue], performances=perfs)
    fig, ax = plt.subplots(figsize=(5, 5))
    panels.draw_segue_graph(ax, comp, top_n=10)
    path = panels.save_figure(fig, tmp_path / "segue.png")
    assert path.stat().st_size > 0


# ---------------------------------------------------------------------------
# segues: out/in degree views + segue_into edge (coverage closure)
# ---------------------------------------------------------------------------


def test_segue_degrees_consistent(compendium):
    edges = segues.segue_edges(compendium)
    out_deg = segues.segue_out_degree(compendium)
    in_deg = segues.segue_in_degree(compendium)
    total = sum(e.count for e in edges)
    assert sum(out_deg.values()) == total
    assert sum(in_deg.values()) == total


def test_segue_edges_capture_segue_into():
    from datetime import date

    from src.integration.reconcile import build_compendium
    from src.models import Performance, Show, Venue, canonical_show_id

    venue = Venue(slug="v", name="V", city="C", state_or_region="CA")
    show = Show(
        slug=canonical_show_id(date(1977, 5, 8), "v"),
        date=date(1977, 5, 8),
        venue_slug="v",
    )
    perfs = [
        Performance(
            show_slug=show.slug,
            song_slug="scarlet_begonias",
            set_number=2,
            position=1,
            segue_into="fire_on_the_mountain",
        ),
        Performance(
            show_slug=show.slug,
            song_slug="fire_on_the_mountain",
            set_number=2,
            position=2,
        ),
    ]
    comp = build_compendium(shows=[show], venues=[venue], performances=perfs)
    edges = segues.segue_edges(comp)
    assert any(
        e.src == "scarlet_begonias" and e.dst == "fire_on_the_mountain" for e in edges
    )
    assert segues.segue_out_degree(comp)["scarlet_begonias"] == 1
    assert segues.segue_in_degree(comp)["fire_on_the_mountain"] == 1


# ---------------------------------------------------------------------------
# opposite category: exercise the returned compose / identity_of closures
# ---------------------------------------------------------------------------


def test_opposite_category_closures(compendium):
    cat = build_show_category(compendium)
    op = opposite(cat)
    obj = next(iter(op.objects))
    # identity_of closure (opposite.py:24) wraps the base identity.
    ident = op.identity_of(obj)
    assert ident.startswith("op(")
    # compose closure (opposite.py:21) composes two opposite arrows.
    composed = op.compose("f", "g")
    assert composed == "op_compose(f,g)"
