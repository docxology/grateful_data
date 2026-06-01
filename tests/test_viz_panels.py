"""Smoke tests for visualization panel builders."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.viz import compose, panels


def _save_draw(tmp_path, name, draw_fn, compendium):
    fig, ax = plt.subplots(figsize=(6, 4))
    draw_fn(ax, compendium)
    path = panels.save_figure(fig, tmp_path / name)
    assert path.stat().st_size > 0
    return path


def test_pretty_label_titlecases_songs_but_keeps_segments_lower():
    assert panels._pretty("scarlet_begonias") == "Scarlet Begonias"
    assert panels._pretty("fire_on_the_mountain") == "Fire on the Mountain"
    assert panels._pretty("i_know_you_rider") == "I Know You Rider"
    # leading word is always capitalised even if a minor word
    assert panels._pretty("the_other_one") == "The Other One"


def test_segue_panel_renders_as_bar_not_blob(tmp_path, compendium):
    # The redesigned segue panel returns True and writes a non-trivial figure
    # (ranked bars), never the old node-link gray blob.
    fig, ax = plt.subplots(figsize=(9, 5.5))
    assert panels.draw_segue_graph(ax, compendium, top_n=10) is True
    path = panels.save_figure(fig, tmp_path / "segue_graph.png")
    assert path.stat().st_size > 0


def test_category_bar_panels_render(tmp_path, compendium):
    for name, fn in (
        ("citation_kinds.png", panels.draw_citation_kinds_pie),
        ("recording_sources.png", panels.draw_recording_sources_pie),
    ):
        fig, ax = plt.subplots(figsize=(7, 4))
        assert fn(ax, compendium) is True
        assert panels.save_figure(fig, tmp_path / name).stat().st_size > 0


def test_song_lifespans_panel_renders(tmp_path, compendium):
    fig, ax = plt.subplots(figsize=(6, 5))
    assert panels.draw_song_lifespans(ax, compendium, top_n=10) is True
    path = panels.save_figure(fig, tmp_path / "song_lifespans.png")
    assert path.stat().st_size > 0


def test_context_timeline_panel_renders(tmp_path, compendium):
    fig, ax = plt.subplots(figsize=(8, 4))
    assert panels.draw_context_timeline(ax, compendium) is True
    path = panels.save_figure(fig, tmp_path / "context_timeline.png")
    assert path.stat().st_size > 0


def test_distribution_and_concentration_panels_render(tmp_path, compendium):
    for name, fn in (
        ("performance_distribution.png", panels.draw_performance_distribution),
        ("repertoire_concentration.png", panels.draw_repertoire_concentration),
        ("venue_concentration.png", panels.draw_venue_concentration),
        ("concentration_uncertainty.png", panels.draw_concentration_uncertainty),
        ("repertoire_embedding.png", panels.draw_repertoire_embedding),
        ("era_repertoire_heatmap.png", panels.draw_era_repertoire_heatmap),
    ):
        fig, ax = plt.subplots(figsize=(8, 4.5))
        assert fn(ax, compendium) is True
        assert panels.save_figure(fig, tmp_path / name).stat().st_size > 0


def test_save_core_figures(tmp_path, compendium):
    _save_draw(tmp_path, "top_songs.png", panels.draw_top_songs, compendium)
    _save_draw(
        tmp_path,
        "shows_year.png",
        panels.draw_shows_and_performances_per_year,
        compendium,
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    labels, _ = panels.draw_cooccurrence_heatmap(ax, compendium, top_n=10)
    assert labels
    panels.save_figure(fig, tmp_path / "cooc.png")
    _save_draw(tmp_path, "functors.png", panels.draw_functor_cardinalities, compendium)
    fig, ax = plt.subplots(figsize=(6, 5))
    panels.draw_transition_matrix(ax, compendium, labels[:5])
    panels.save_figure(fig, tmp_path / "trans.png")


def test_save_extended_figures(tmp_path, compendium):
    _save_draw(tmp_path, "composer.png", panels.draw_composer_attribution, compendium)
    _save_draw(tmp_path, "segue.png", panels.draw_segue_graph, compendium)
    _save_draw(tmp_path, "era.png", panels.draw_shows_by_era, compendium)
    _save_draw(tmp_path, "citations.png", panels.draw_citation_kinds_pie, compendium)
    _save_draw(
        tmp_path,
        "cardinalities.png",
        panels.draw_functor_cardinalities_with_presheaf,
        compendium,
    )
    assert panels.categorical_summary(compendium)[
        "active_lineup_presheaf_expected_non_monotone"
    ]


def test_save_more_figures(tmp_path, compendium):
    _save_draw(tmp_path, "geo.png", panels.draw_geo_scatter, compendium)
    _save_draw(tmp_path, "positions.png", panels.draw_set_positions, compendium)
    _save_draw(
        tmp_path,
        "stationary.png",
        lambda ax, c: panels.draw_stationary_top(ax, c, top_n=5),
        compendium,
    )
    _save_draw(
        tmp_path,
        "centrality.png",
        lambda ax, c: panels.draw_centrality_top(ax, c, top_n=5),
        compendium,
    )
    _save_draw(tmp_path, "releases.png", panels.draw_releases_timeline, compendium)
    _save_draw(tmp_path, "context.png", panels.draw_context_timeline, compendium)
    _save_draw(
        tmp_path,
        "performance_distribution.png",
        panels.draw_performance_distribution,
        compendium,
    )
    _save_draw(
        tmp_path,
        "repertoire_concentration.png",
        panels.draw_repertoire_concentration,
        compendium,
    )
    _save_draw(
        tmp_path,
        "venue_concentration.png",
        panels.draw_venue_concentration,
        compendium,
    )
    _save_draw(
        tmp_path,
        "concentration_uncertainty.png",
        panels.draw_concentration_uncertainty,
        compendium,
    )
    _save_draw(
        tmp_path,
        "repertoire_embedding.png",
        panels.draw_repertoire_embedding,
        compendium,
    )
    _save_draw(
        tmp_path,
        "era_repertoire_heatmap.png",
        panels.draw_era_repertoire_heatmap,
        compendium,
    )
    _save_draw(
        tmp_path,
        "claim_evidence_matrix.png",
        panels.draw_claim_evidence_matrix,
        compendium,
    )
    _save_draw(tmp_path, "tours.png", panels.draw_tours_top, compendium)
    _save_draw(tmp_path, "era_density.png", panels.draw_era_density, compendium)
    _save_draw(tmp_path, "gantt.png", panels.draw_personnel_gantt, compendium)
    _save_draw(tmp_path, "sentiment.png", panels.draw_sentiment_by_kind, compendium)
    _save_draw(
        tmp_path, "recording_pie.png", panels.draw_recording_sources_pie, compendium
    )
    _save_draw(tmp_path, "themes.png", panels.draw_lyric_themes, compendium)
    _save_draw(tmp_path, "diversity.png", panels.draw_lineup_diversity, compendium)


def test_save_mosaic(tmp_path, compendium):
    path = compose.save_mosaic(compendium, tmp_path / "mosaic.png")
    assert path.exists()
    assert path.stat().st_size > 1000
