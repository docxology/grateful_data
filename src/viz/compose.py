"""Mosaic figure composition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from ..analysis import geo, lyrics, segues, stats, tours
from ..integration.reconcile import Compendium
from ..tier import resolve_seed_dir
from . import panels, style


def build_mosaic(comp: Compendium) -> plt.Figure:
    s = stats.compute(comp, top_n=15)
    freq = lyrics.theme_frequencies(comp)
    edges = segues.segue_edges(comp)
    geo_map = geo.load_geo()
    dates = sorted(sh.date.isoformat() for sh in comp.shows)
    span = f"{dates[0]} … {dates[-1]}" if dates else "n/a"
    tier_label = style.tier_phrase(comp)

    fig = plt.figure(figsize=style.MOSAIC_FIGSIZE)
    grid = fig.add_gridspec(
        9,
        3,
        hspace=0.66,
        wspace=0.36,
        height_ratios=[0.64, 0.92, 1.30, 1.22, 1.25, 1.18, 1.18, 1.18, 1.0],
    )

    ax_t = fig.add_subplot(grid[0, :])
    ax_t.axis("off")
    ax_t.text(
        0.0,
        0.76,
        "The Music Never Stopped — Grateful Data Compendium",
        ha="left",
        fontsize=22,
        fontweight="bold",
    )
    ax_t.text(
        0.0,
        0.48,
        f"{tier_label} · {span}\n"
        f"{s.n_shows:,} shows · {s.n_songs:,} songs · {s.n_performances:,} performance rows · "
        f"{s.n_venues:,} venues · {s.n_recordings:,} recordings · {s.n_citations:,} citations",
        ha="left",
        fontsize=12,
        color="#374151",
    )
    ax_t.text(
        0.0,
        0.24,
        "Design critique pass: fewer, larger story panels; standalone figures carry the full detail. "
        "No lyric text or audio bundled.",
        ha="left",
        fontsize=10,
        color="#6B7280",
    )
    ax_t.text(
        0.0,
        0.06,
        panels.categorical_summary_text(comp),
        ha="left",
        fontsize=10,
        color="#111827",
        fontstyle="italic",
    )

    ax = fig.add_subplot(grid[1, :])
    panels.draw_context_timeline(ax, comp)
    ax.set_title("Scope + Time: shows per year with context markers")

    ax = fig.add_subplot(grid[2, 0])
    panels.draw_top_songs(ax, comp, top_n=15)
    ax.set_title("Repertoire: most-performed songs")
    ax.tick_params(axis="y", labelsize=7)

    ax = fig.add_subplot(grid[2, 1])
    panels.draw_repertoire_concentration(ax, comp)
    ax.set_title("Repertoire: concentration curve")

    ax = fig.add_subplot(grid[2, 2])
    panels.draw_repertoire_embedding(ax, comp)
    ax.set_title("Repertoire: exploratory SVD embedding")

    ax = fig.add_subplot(grid[3, 0])
    panels.draw_performance_distribution(ax, comp)
    ax.set_title("Statistical shape: rows per show")

    ax = fig.add_subplot(grid[3, 1])
    panels.draw_concentration_uncertainty(ax, comp)
    ax.set_title("Statistical shape: bootstrap intervals")

    ax = fig.add_subplot(grid[3, 2])
    panels.draw_repertoire_topn_sensitivity(ax, comp)
    ax.set_title("Statistical shape: top-N sensitivity")

    ax = fig.add_subplot(grid[4, :2])
    panels.draw_segue_graph(ax, comp, top_n=18)
    ax.set_title("Transitions: explicit segue edges")

    ax = fig.add_subplot(grid[4, 2])
    panels.draw_transition_sensitivity(ax, comp)
    ax.set_title("Transitions: support sensitivity")

    ax = fig.add_subplot(grid[5, 0])
    if panels.draw_stationary_top(ax, comp, top_n=12):
        ax.set_title("Transitions: stationary mass")

    ax = fig.add_subplot(grid[5, 1])
    if panels.draw_centrality_top(ax, comp, top_n=12):
        ax.set_title("Transitions: association centrality")
        ax.tick_params(axis="y", labelsize=7)

    ax = fig.add_subplot(grid[5, 2])
    panels.draw_functor_cardinalities_with_presheaf(ax, comp)
    ax.set_title("Evidence: categorical checks")

    ax = fig.add_subplot(grid[6, :2])
    panels.draw_geo_scatter(ax, comp, geo_map=geo_map)
    ax.set_title("Geography: geocoded venues")

    ax = fig.add_subplot(grid[6, 2])
    panels.draw_venue_identity_review(ax, comp)
    ax.set_title("Geography: venue identity review")

    ax = fig.add_subplot(grid[7, 0])
    panels.draw_citation_kinds_pie(ax, comp)
    ax.set_title("Evidence: citation mix")

    ax = fig.add_subplot(grid[7, 1])
    panels.draw_recording_sources_pie(ax, comp)
    ax.set_title("Evidence: recording sources")

    ax = fig.add_subplot(grid[7, 2])
    if panels.draw_lyric_themes(ax, comp, top_n=12):
        ax.set_title("Evidence: lyric pointer themes")
        ax.tick_params(axis="y", labelsize=7)

    ax = fig.add_subplot(grid[8, :])
    ax.axis("off")
    data_tier = resolve_seed_dir()
    geo_path = f"data/{data_tier.name}/venue_geo.json"
    reviews_path = f"data/{data_tier.name}/reviews.json"
    rows: list[list[Any]] = [
        ["Layer", "Count", "Source / note"],
        ["Shows", f"{s.n_shows:,}", "gdshowsdb + gap-fill sources"],
        ["Performance rows", f"{s.n_performances:,}", "performances.json / derived"],
        ["Songs", f"{s.n_songs:,}", "gdshowsdb + alex_allan"],
        ["Venues", f"{s.n_venues:,}", "derived from show ingestion"],
        ["Venue geo entries", f"{len(geo_map):,}", geo_path],
        ["Recordings", f"{s.n_recordings:,}", "internet_archive_lma + curated"],
        ["Releases", f"{s.n_releases:,}", "wikipedia + curated"],
        [
            "Lyric pointers",
            f"{len(comp.lyric_pointers):,}",
            "pointer metadata; no lyrics",
        ],
        ["Reviews", f"{len(comp.reviews):,}", reviews_path],
        ["Citations", f"{s.n_citations:,}", "bibliography + references.bib"],
        ["Segue edges", f"{len(edges):,}", "explicit segue_into markers"],
        ["Lyric themes", f"{len(freq):,}", "derived from pointer set"],
        ["Figure raw data", "CSV + JSON", "output/data/figures/"],
        ["Honesty boundary", "ON", "src/honesty.py"],
        ["Schema validation", "ON", "src/validation.py"],
    ]
    table = ax.table(
        cellText=[[str(c) for c in r] for r in rows[1:]],
        colLabels=rows[0],
        loc="center",
        cellLoc="left",
        colColours=["#E5E7EB"] * 3,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.0, 1.35)

    return fig


def save_mosaic(comp: Compendium, path: Path) -> Path:
    fig = build_mosaic(comp)
    return panels.save_figure(fig, path, dpi=style.MOSAIC_DPI, comp=comp)
