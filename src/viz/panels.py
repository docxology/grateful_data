"""Reusable matplotlib panel builders (data in, Axes out)."""

from __future__ import annotations

from collections import Counter
from datetime import date as _date
from pathlib import Path
from textwrap import shorten
from typing import TYPE_CHECKING, Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..analysis import (
    bustouts,
    centrality,
    composers,
    cooccurrence,
    distributions,
    eras,
    exploratory,
    first_principles,
    geo,
    lyrics,
    personnel_timeline,
    positions,
    repertoire,
    reviews,
    segues,
    stationary,
    stats,
    timeseries,
    tours,
    transitions,
    venues,
)
from ..cattheory.functors import (
    active_lineup_presheaf,
    is_monotone,
    lineup_functor,
    setlist_functor,
)
from ..cattheory.natural import naturality_square_holds
from ..integration.reconcile import Compendium
from . import style

if TYPE_CHECKING:
    pass


def _pretty(slug: str) -> str:
    """Human-readable song/segment label from a canonical slug.

    ``scarlet_begonias`` -> ``Scarlet Begonias``; segment markers stay lower
    (``drums``, ``space``) since that is how they read in setlists.
    """
    title = slug.replace("_", " ")
    # Title-case words but leave short connectors lowercased for readability.
    minor = {"the", "of", "in", "on", "a", "and", "to", "my"}
    words = title.split()
    out = [w if (i and w in minor) else w.capitalize() for i, w in enumerate(words)]
    return " ".join(out)


def _draw_empty_panel(ax: Axes, message: str, *, title: str = "") -> bool:
    ax.axis("off")
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=10,
        color="#6b7280",
        wrap=True,
    )
    if title:
        ax.set_title(title)
    return True


def save_figure(
    fig: Figure, path: Path, *, dpi: int = style.FIG_DPI, comp: Compendium | None = None
) -> Path:
    """Save a figure to disk, optionally stamping the shared provenance footer.

    Pass ``comp`` to add the uniform "seed compendium · n=… shows" footer so
    every figure carries identical, honest provenance.
    """
    if comp is not None:
        style.add_provenance(fig, comp)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path


def draw_shows_and_performances_per_year(ax: Axes, comp: Compendium) -> None:
    s = stats.compute(comp, top_n=15)
    years = list(s.shows_per_year.keys())
    show_counts = list(s.shows_per_year.values())
    perf_per_year = timeseries.performances_per_year(comp)
    perf_counts = [perf_per_year.get(y, 0) for y in years]
    ax.bar(years, show_counts, label="Shows", color=style.COLORS["blue"])
    ax2 = ax.twinx()
    ax2.plot(
        years, perf_counts, color=style.COLORS["red"], marker="o", label="Performances"
    )
    ax.set_xlabel("Year")
    ax.set_ylabel("Shows per year")
    ax2.set_ylabel("Performances per year")
    ax.set_title("Shows and performances per year")


def draw_shows_per_year(ax: Axes, comp: Compendium) -> None:
    s = stats.compute(comp, top_n=15)
    years = sorted(s.shows_per_year)
    ax.bar(years, [s.shows_per_year[y] for y in years], color=style.COLORS["blue"])
    ax.set_title("Shows per year")
    ax.tick_params(axis="x", rotation=45, labelsize=7)


def draw_performances_per_year(ax: Axes, comp: Compendium) -> None:
    py_perf = timeseries.performances_per_year(comp)
    py_years = sorted(py_perf)
    ax.plot(
        py_years,
        [py_perf[y] for y in py_years],
        marker="o",
        color=style.COLORS["red"],
        lw=1.5,
    )
    ax.set_title("Performances per year")
    ax.tick_params(axis="x", rotation=45, labelsize=7)


def draw_performance_distribution(ax: Axes, comp: Compendium) -> bool:
    """Distribution of performance rows per show, including empty setlists."""
    per_show = distributions.performance_rows_per_show(comp)
    if not per_show:
        return _draw_empty_panel(
            ax,
            "No shows available for per-show distribution.",
            title="Performance rows per show",
        )
    values = list(per_show.values())
    nonzero = [value for value in values if value > 0]
    summary = distributions.performance_distribution(comp)
    if not nonzero:
        return _draw_empty_panel(
            ax,
            "All shows have empty setlists in this tier.",
            title="Performance rows per show",
        )
    max_value = max(nonzero)
    if max_value <= 60:
        bins = np.arange(0.5, max_value + 1.5, 1)
    else:
        bins = min(30, max(8, int(np.sqrt(len(nonzero)))))
    ax.hist(nonzero, bins=bins, color=style.COLORS["indigo"], alpha=0.82)
    ax.axvline(
        summary.per_show.median,
        color=style.COLORS["red"],
        linestyle="--",
        lw=1.4,
        label=f"median {summary.per_show.median:g}",
    )
    ax.axvline(
        summary.per_show.p90,
        color=style.COLORS["amber"],
        linestyle=":",
        lw=1.6,
        label=f"p90 {summary.per_show.p90:g}",
    )
    ax.set_xlabel(f"Performance rows per show ({style.tier_short(comp)})")
    ax.set_ylabel("Shows with non-empty setlists")
    ax.set_title(
        "Non-empty setlist-size distribution "
        f"(overall mean {summary.per_show.mean:.1f})"
    )
    empty_share = summary.n_zero_performance_shows / len(values) if values else 0.0
    ax.text(
        0.98,
        0.96,
        f"Empty setlists: {summary.n_zero_performance_shows:,}\n"
        f"({empty_share:.0%} of shows)",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color="#374151",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#d1d5db",
            "alpha": 0.92,
        },
    )
    ax.legend(frameon=False, fontsize=7)
    return True


def _draw_concentration_curve(
    ax: Axes,
    counts: dict[str, int],
    *,
    summary: distributions.ConcentrationSummary,
    title: str,
    xlabel: str,
    color: str,
) -> bool:
    if not counts:
        return _draw_empty_panel(ax, "No counts available.", title=title)
    values = sorted(counts.values(), reverse=True)
    total = sum(values)
    if total <= 0:
        return _draw_empty_panel(ax, "All counts are zero.", title=title)
    cumulative = np.cumsum(values) / total * 100.0
    x = np.arange(1, len(values) + 1)
    ax.plot(x, cumulative, color=color, lw=2)
    ax.fill_between(x, cumulative, color=color, alpha=0.12)
    for threshold, n_items in (
        (50, summary.n_for_50_pct),
        (80, summary.n_for_80_pct),
    ):
        ax.axhline(threshold, color="#9ca3af", lw=0.8, linestyle="--")
        ax.axvline(n_items, color="#9ca3af", lw=0.8, linestyle="--")
        ax.annotate(
            f"{n_items:,} items for {threshold}%",
            (n_items, threshold),
            xytext=(5, 5 if threshold == 50 else -14),
            textcoords="offset points",
            fontsize=7,
            color="#374151",
        )
    ax.set_ylim(0, 102)
    ax.set_xlim(1, len(values))
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Cumulative share of rows")
    ax.set_title(
        f"{title} (Gini {summary.gini:.2f}; top 10%={summary.top_10_share_pct:.0f}%)"
    )
    ax.grid(True, alpha=0.2)
    return True


def draw_repertoire_concentration(ax: Axes, comp: Compendium) -> bool:
    """Cumulative share of performance rows by ranked song."""
    counts = distributions.song_performance_counts(comp)
    summary = distributions.song_performance_concentration(comp)
    return _draw_concentration_curve(
        ax,
        counts,
        summary=summary,
        title="Repertoire concentration",
        xlabel="Songs ranked by performance count (segments excluded)",
        color=style.COLORS["green"],
    )


def draw_venue_concentration(ax: Axes, comp: Compendium) -> bool:
    """Cumulative share of shows by ranked venue."""
    counts = distributions.venue_show_counts(comp)
    summary = distributions.venue_show_concentration(comp)
    return _draw_concentration_curve(
        ax,
        counts,
        summary=summary,
        title="Venue concentration",
        xlabel="Venues ranked by show count",
        color=style.COLORS["sky"],
    )


def draw_concentration_uncertainty(ax: Axes, comp: Compendium) -> bool:
    """Bootstrap intervals for repertoire and venue concentration metrics."""
    report = distributions.concentration_uncertainty_report(comp)
    families = (
        ("Song", report["song_performance_concentration"]),
        ("Venue", report["venue_show_concentration"]),
    )
    rows: list[tuple[str, float, float, float, str]] = []
    for family, payload in families:
        if not isinstance(payload, dict):
            continue
        gini = payload.get("gini", {})
        top10 = payload.get("top_10_share_pct", {})
        if isinstance(gini, dict):
            rows.append(
                (
                    f"{family} Gini",
                    float(gini.get("point", 0.0)),
                    float(gini.get("low", 0.0)),
                    float(gini.get("high", 0.0)),
                    style.COLORS["green"] if family == "Song" else style.COLORS["sky"],
                )
            )
        if isinstance(top10, dict):
            rows.append(
                (
                    f"{family} top 10% share",
                    float(top10.get("point", 0.0)) / 100.0,
                    float(top10.get("low", 0.0)) / 100.0,
                    float(top10.get("high", 0.0)) / 100.0,
                    style.COLORS["purple"]
                    if family == "Song"
                    else style.COLORS["amber"],
                )
            )
    if not rows:
        return _draw_empty_panel(
            ax,
            "No concentration intervals available.",
            title="Concentration uncertainty",
        )
    y = np.arange(len(rows))[::-1]
    for yi, (label, point, low, high, color) in zip(y, rows):
        ax.errorbar(
            point,
            yi,
            xerr=[[max(0.0, point - low)], [max(0.0, high - point)]],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=2,
            capsize=4,
        )
        ax.annotate(
            f"{point:.2f} [{low:.2f}, {high:.2f}]",
            (high, yi),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=7,
            color="#374151",
        )
    ax.set_yticks(y)
    ax.set_yticklabels([label for label, *_rest in rows], fontsize=8)
    ax.set_xlim(0, min(1.05, max(high for _l, _p, _lo, high, _c in rows) + 0.15))
    ax.set_xlabel("Coefficient/share on 0-1 scale")
    ax.set_title("Bootstrap intervals for concentration metrics")
    ax.grid(axis="x", alpha=0.25)
    return True


def draw_transition_sensitivity(ax: Axes, comp: Compendium) -> bool:
    """Transition-model support retention with and without generic segments."""
    report = transitions.transition_sensitivity_report(comp, include_era_models=False)
    rows = report.get("segment_marker_policies", [])
    if not isinstance(rows, list) or not rows:
        return _draw_empty_panel(
            ax,
            "No transition-sensitivity rows available.",
            title="Transition sensitivity",
        )
    for exclude_segments, color, label in (
        (False, style.COLORS["purple"], "incl. segments"),
        (True, style.COLORS["green"], "excl. segments"),
    ):
        policy_rows = [
            row
            for row in rows
            if isinstance(row, dict) and bool(row.get("exclude_segments")) == exclude_segments
        ]
        if not policy_rows:
            continue
        policy_rows.sort(key=lambda row: int(row["min_predecessor_support"]))
        x = [int(row["min_predecessor_support"]) for row in policy_rows]
        y_edges = [
            100.0
            * int(row["n_supported_edges"])
            / max(1, int(row["n_nonzero_edges"]))
            for row in policy_rows
        ]
        y_predecessors = [
            100.0
            * int(row["n_supported_predecessors"])
            / max(1, int(row["n_songs"]))
            for row in policy_rows
        ]
        ax.plot(x, y_edges, marker="o", lw=2, color=color, label=f"{label}: edges")
        ax.plot(
            x,
            y_predecessors,
            marker="s",
            lw=1.4,
            linestyle="--",
            color=color,
            alpha=0.82,
            label=f"{label}: predecessor rows",
        )
    ax.set_xscale("log")
    ax.set_xticks(sorted({int(row["min_predecessor_support"]) for row in rows if isinstance(row, dict)}))
    ax.get_xaxis().set_major_formatter(
        mticker.FuncFormatter(lambda value, _pos: f"{int(value):d}")
    )
    ax.set_ylim(0, 105)
    ax.set_xlabel("Minimum observed predecessor support")
    ax.set_ylabel("Share retained (%)")
    ax.set_title("Transition support sensitivity")
    ax.grid(True, which="both", axis="x", alpha=0.25)
    ax.grid(True, axis="y", alpha=0.2)
    ax.legend(frameon=False, fontsize=7, ncols=2, loc="lower left")
    return True


def draw_repertoire_topn_sensitivity(ax: Axes, comp: Compendium) -> bool:
    """How top-N repertoire cuts change total and era-level coverage."""
    report = repertoire.repertoire_topn_sensitivity(comp)
    rows = report.get("rows", [])
    if not isinstance(rows, list) or not rows:
        return _draw_empty_panel(
            ax,
            "No repertoire top-N sensitivity rows available.",
            title="Repertoire top-N sensitivity",
        )
    rows = sorted(rows, key=lambda row: int(row["top_n"]))
    x = [int(row["top_n"]) for row in rows]
    perf_share = [float(row["performance_share_pct"]) for row in rows]
    era_min: list[float] = []
    era_max: list[float] = []
    era_mean: list[float] = []
    for row in rows:
        coverages = [
            float(era_row["era_performance_share_pct"])
            for era_row in row.get("era_coverage", [])
            if isinstance(era_row, dict)
        ]
        era_min.append(min(coverages) if coverages else 0.0)
        era_max.append(max(coverages) if coverages else 0.0)
        era_mean.append(sum(coverages) / len(coverages) if coverages else 0.0)
    ax.fill_between(x, era_min, era_max, color=style.COLORS["sky"], alpha=0.18, label="Era coverage range")
    ax.plot(x, era_mean, color=style.COLORS["sky"], linestyle="--", marker="s", lw=1.6, label="Mean era coverage")
    ax.plot(x, perf_share, color=style.COLORS["green"], marker="o", lw=2.2, label="Total non-segment share")
    for xi, yi in zip(x, perf_share):
        ax.annotate(f"{yi:.0f}%", (xi, yi), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=7)
    ax.set_ylim(0, min(105, max(max(era_max), max(perf_share)) + 16))
    ax.set_xticks(x)
    ax.set_xlabel("Top-N song cut")
    ax.set_ylabel("Performance-row share (%)")
    ax.set_title("Repertoire top-N sensitivity")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    return True


def draw_venue_identity_review(ax: Axes, comp: Compendium) -> bool:
    """Report-only venue alias and collision diagnostics."""
    review = venues.venue_identity_review(comp)
    summary = review.get("summary", {})
    if not isinstance(summary, dict) or not summary:
        return _draw_empty_panel(
            ax,
            "No venue identity review rows available.",
            title="Venue identity review",
        )
    rows = [
        ("Venue slugs", int(summary.get("n_venue_slugs", 0)), style.COLORS["sky"]),
        ("Alias slugs present", int(summary.get("n_alias_slugs_present", 0)), style.COLORS["green"]),
        ("Would collapse", int(summary.get("n_venues_collapsed", 0)), style.COLORS["amber"]),
        (
            "Same-date canonical collisions",
            int(summary.get("n_ambiguous_same_date_collisions", 0)),
            style.COLORS["red"],
        ),
    ]
    labels = [row[0] for row in rows]
    values = [row[1] for row in rows]
    colors = [row[2] for row in rows]
    y = np.arange(len(rows))[::-1]
    bars = ax.barh(y, values, color=colors, alpha=0.86)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Count")
    ax.set_title("Venue identity diagnostics (report-only)")
    max_value = max(values) if values else 1
    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:,}",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color="#374151",
        )
    ax.set_xlim(0, max_value * 1.22)
    ax.grid(axis="x", alpha=0.25)
    ax.text(
        0.98,
        0.05,
        f"Mean collision setlist Jaccard: {float(summary.get('mean_collision_setlist_jaccard', 0.0)):.3f}\n"
        "Alias map is conservative; compendium rows are not rewritten.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color="#374151",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#d1d5db",
            "alpha": 0.92,
        },
    )
    return True


def draw_repertoire_embedding(ax: Axes, comp: Compendium) -> bool:
    """Exploratory SVD embedding of era-by-song repertoire profiles."""
    emb = exploratory.repertoire_embedding(comp, top_n=80, n_clusters=5)
    if not emb.songs:
        return _draw_empty_panel(
            ax,
            "No repertoire rows available for exploratory embedding.",
            title="Exploratory repertoire embedding",
        )
    palette = plt.get_cmap("tab10")
    clusters = sorted({song.cluster for song in emb.songs})
    for cluster in clusters:
        rows = [song for song in emb.songs if song.cluster == cluster]
        ax.scatter(
            [song.x for song in rows],
            [song.y for song in rows],
            s=[
                max(24, min(180, 10 + np.sqrt(song.n_performances) * 6))
                for song in rows
            ],
            color=palette(cluster % 10),
            alpha=0.78,
            edgecolors="white",
            linewidth=0.5,
            label=f"Cluster {cluster} (n={len(rows)})",
        )
    label_rows = sorted(
        emb.songs, key=lambda song: (-song.n_performances, song.song_slug)
    )[:10]
    offsets = ((8, 8), (8, -14), (-8, 8), (-8, -14), (10, 0), (-10, 0))
    for idx, song in enumerate(label_rows):
        ox, oy = offsets[idx % len(offsets)]
        ax.annotate(
            shorten(song.title, width=19, placeholder="..."),
            (song.x, song.y),
            xytext=(ox, oy),
            textcoords="offset points",
            ha="left" if ox >= 0 else "right",
            fontsize=7,
            color="#111827",
            bbox={
                "boxstyle": "round,pad=0.12",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
            },
        )
    ax.axhline(0, color="#9ca3af", lw=0.7, alpha=0.6)
    ax.axvline(0, color="#9ca3af", lw=0.7, alpha=0.6)
    ax.set_xlabel(f"SVD component 1 ({emb.component_variance_share[0]:.0%} variance)")
    ax.set_ylabel(f"SVD component 2 ({emb.component_variance_share[1]:.0%} variance)")
    ax.set_title("Exploratory repertoire embedding (top songs; segments excluded)")
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    ax.text(
        0.01,
        0.01,
        "Pattern discovery only; coordinates from centered log era-count profiles.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7,
        color="#6b7280",
    )
    return True


def draw_era_repertoire_heatmap(ax: Axes, comp: Compendium) -> bool:
    """Era-by-top-song normalized repertoire intensity heatmap."""
    matrix = exploratory.era_song_matrix(comp, top_n=20)
    if matrix.counts.size == 0:
        return _draw_empty_panel(
            ax,
            "No era-by-song matrix available.",
            title="Era repertoire heatmap",
        )
    data = matrix.normalized * 100.0
    im = ax.imshow(data, aspect="auto", cmap="cividis")
    ax.figure.colorbar(
        im, ax=ax, fraction=0.046, pad=0.04, label="Share of era performance rows (%)"
    )
    ax.set_xticks(range(len(matrix.song_slugs)))
    ax.set_xticklabels(
        [_pretty(slug) for slug in matrix.song_slugs],
        rotation=50,
        ha="right",
        fontsize=8,
    )
    ax.set_yticks(range(len(matrix.eras)))
    ax.set_yticklabels(matrix.eras, fontsize=8)
    ax.set_title("Era-normalized repertoire intensity (top songs)")
    ax.set_xlabel("Song (segments excluded)")
    ax.set_ylabel("Era")
    return True


def draw_claim_evidence_matrix(ax: Axes, comp: Compendium) -> bool:
    """First-principles map from claim classes to evidence artifacts."""
    matrix, claim_classes, artifact_families = first_principles.claim_evidence_matrix(
        comp
    )
    data = np.array(matrix, dtype=float)
    if data.size == 0:
        return _draw_empty_panel(
            ax,
            "No claim-evidence rows available.",
            title="Claim evidence matrix",
        )
    im = ax.imshow(data, aspect="auto", cmap="YlGnBu", vmin=0)
    cbar = ax.figure.colorbar(
        im,
        ax=ax,
        fraction=0.046,
        pad=0.04,
        label="claim families",
        ticks=range(int(data.max()) + 1),
    )
    cbar.ax.tick_params(labelsize=8)
    ax.set_xticks(range(len(artifact_families)))
    ax.set_xticklabels(artifact_families, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(claim_classes)))
    ax.set_yticklabels(claim_classes, fontsize=8)
    max_value = float(data.max()) if data.size else 0.0
    for row_idx, claim_class in enumerate(claim_classes):
        for col_idx, _family in enumerate(artifact_families):
            value = int(data[row_idx, col_idx])
            if value == 0:
                continue
            color = "white" if max_value and value > max_value / 2 else "#111827"
            ax.text(
                col_idx,
                row_idx,
                str(value),
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                color=color,
            )
    ax.set_xlabel("Primary validation artifact family")
    ax.set_ylabel("Claim class")
    ax.set_title("First-principles claim evidence map")
    ax.text(
        0.62,
        0.98,
        "Counts are claim families, not corpus observations.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=7,
        color="#374151",
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "white",
            "edgecolor": "#d1d5db",
            "alpha": 0.9,
        },
    )
    return True


def draw_context_timeline(ax: Axes, comp: Compendium) -> bool:
    """Shows per year with non-quantitative historical context markers.

    The bars are computed from the compendium. The milestone labels are a
    small, cited interpretive overlay used in the manuscript to orient the
    data against archival, sound-technology, recording, and public-recognition
    history; they are not ingested as performance rows.
    """
    s = stats.compute(comp, top_n=15)
    years = sorted(s.shows_per_year)
    if not years:
        return _draw_empty_panel(
            ax,
            "No shows available for context timeline.",
            title="Shows per year with context markers",
        )
    counts = [s.shows_per_year[y] for y in years]
    ax.bar(years, counts, color=style.COLORS["blue"], alpha=0.72, width=0.85)

    milestones = [
        (1965, "Warlocks/\nAcid Tests"),
        (1969, "Live/Dead"),
        (1970, "Workingman's/\nAmerican Beauty"),
        (1974, "Wall of\nSound"),
        (1984, "Taper\nsection"),
        (1987, "Touch of\nGrey"),
        (1995, "Final show/\nGarcia"),
    ]
    y_max = max(counts) or 1
    ax.set_ylim(0, y_max * 1.45)
    label_rows = (1.23, 1.09, 1.34)
    for idx, (year, label) in enumerate(milestones):
        if year < years[0] or year > years[-1]:
            continue
        ax.axvline(year, color="#111827", lw=0.8, alpha=0.35, zorder=0)
        ax.annotate(
            label,
            xy=(year, y_max * 1.01),
            xytext=(year, y_max * label_rows[idx % len(label_rows)]),
            textcoords="data",
            ha="center",
            va="bottom",
            fontsize=7,
            color="#111827",
            linespacing=0.95,
            arrowprops={
                "arrowstyle": "-",
                "color": "#6b7280",
                "lw": 0.6,
                "alpha": 0.75,
            },
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "edgecolor": "#d1d5db",
                "alpha": 0.9,
            },
        )
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Shows ({style.tier_short(comp)})")
    ax.set_title("Shows per year with historical context markers", pad=10)
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.margins(x=0.02)
    return True


def draw_top_songs(ax: Axes, comp: Compendium, *, top_n: int = 15) -> None:
    s = stats.compute(comp, top_n=top_n)
    top_slugs = [slug for slug, _ in s.top_songs]
    top_labels = [_pretty(slug) for slug in top_slugs]
    top_counts = [c for _, c in s.top_songs]
    ax.barh(top_labels[::-1], top_counts[::-1], color=style.COLORS["green"])
    ax.set_xlabel(f"Performances ({style.tier_short(comp)})")
    ax.set_title(f"Most-performed songs — {style.tier_phrase(comp)}")
    # Honesty: segment markers (drums/space/…) are excluded from this
    # repertoire ranking; annotate with their counts so nothing is hidden.
    if s.segment_marker_counts:
        note = "excl. segments: " + ", ".join(
            f"{slug} {n}" for slug, n in s.segment_marker_counts
        )
        ax.annotate(
            note,
            xy=(1.0, -0.12),
            xycoords="axes fraction",
            ha="right",
            va="top",
            fontsize=6,
            color="#6b7280",
        )


def draw_cooccurrence_heatmap(
    ax: Axes, comp: Compendium, *, top_n: int = 25
) -> tuple[list[str], np.ndarray]:
    songs, m = cooccurrence.cooccurrence_matrix(comp, exclude_segments=True)
    diag = np.diag(m)
    top_idx = np.argsort(-diag)[:top_n]
    sub = m[np.ix_(top_idx, top_idx)]
    labels = [songs[i] for i in top_idx]
    pretty_labels = [_pretty(slug) for slug in labels]
    im = ax.imshow(sub, cmap="viridis")
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="co-occurrences")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(pretty_labels, rotation=90, fontsize=7)
    ax.set_yticklabels(pretty_labels, fontsize=7)
    ax.set_title(f"Song co-occurrence among top {top_n} songs (segments excluded)")
    return labels, sub


def draw_functor_cardinalities(ax: Axes, comp: Compendium) -> None:
    f_set = setlist_functor(comp)
    f_lin = lineup_functor(comp)
    f_dates = sorted(f_set.keys())
    f_sizes = [len(f_set[d]) for d in f_dates]
    l_sizes = [len(f_lin[d]) for d in f_dates]
    ax.plot(
        range(len(f_dates)), f_sizes, label="|F_setlist|", color=style.COLORS["purple"]
    )
    ax2 = ax.twinx()
    ax2.plot(
        range(len(f_dates)), l_sizes, color=style.COLORS["amber"], label="|F_lineup|"
    )
    ax.set_xlabel("Show index (chronological)")
    ax.set_ylabel("Cumulative setlist size")
    ax2.set_ylabel("Cumulative roster size")
    ax.set_title("Cumulative setlist and lineup functor cardinalities")


def draw_transition_matrix(ax: Axes, comp: Compendium, labels: list[str]) -> None:
    tm = transitions.fit(comp, exclude_segments=True)
    idx = [tm.song_slugs.index(slug) for slug in labels if slug in tm.song_slugs]
    sub_t = tm.transition_matrix[np.ix_(idx, idx)]
    sub_labels = [tm.song_slugs[i] for i in idx]
    pretty_labels = [_pretty(slug) for slug in sub_labels]
    im = ax.imshow(sub_t, cmap="magma")
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="P(next | current)")
    ax.set_xticks(range(len(sub_labels)))
    ax.set_yticks(range(len(sub_labels)))
    ax.set_xticklabels(pretty_labels, rotation=90, fontsize=7)
    ax.set_yticklabels(pretty_labels, fontsize=7)
    ax.set_title("First-order Markov transitions (segments excluded)")


def draw_composer_attribution(ax: Axes, comp: Compendium, *, top_n: int = 12) -> None:
    cs = composers.composer_song_counts(comp)
    cps = composers.composer_performance_counts(comp)
    top = list(cs.keys())[:top_n]
    x = np.arange(len(top))
    ax.bar(
        x - 0.2,
        [cs[k] for k in top],
        width=0.4,
        label="songs written",
        color=style.COLORS["blue"],
    )
    ax.bar(
        x + 0.2,
        [cps.get(k, 0) for k in top],
        width=0.4,
        label="weighted performances",
        color=style.COLORS["red"],
    )
    ax.set_xticks(x)
    ax.set_xticklabels(top, rotation=30, ha="right")
    ax.set_title(f"Composer credits — {style.tier_phrase(comp)}")
    ax.legend()


def draw_segue_graph(ax: Axes, comp: Compendium, *, top_n: int = 15) -> bool:
    """Most frequent segues as a ranked horizontal bar chart ``A -> B``.

    A node-link layout with linearly weight-scaled arrows collapses into an
    unreadable blob at archival scale (the top edge alone occurs ~1200 times).
    A ranked bar chart answers the actual question — *which song-to-song segues
    happen most often* — unambiguously, with the count on the axis.
    """
    edges = segues.segue_edges(comp)
    top_edges = edges[:top_n]
    n_segues = sum(1 for p in comp.performances if p.segue_into)
    if not top_edges:
        return _draw_empty_panel(
            ax,
            "No segue (>/->) transitions are encoded\nin the loaded setlists.",
            title="Most frequent segues",
        )
    labels = [f"{_pretty(e.src)}  →  {_pretty(e.dst)}" for e in top_edges]
    counts = [e.count for e in top_edges]
    y = range(len(top_edges))
    bars = ax.barh(list(y)[::-1], counts[::-1], color=style.COLORS["purple"])
    ax.set_yticks(list(y)[::-1])
    ax.set_yticklabels(labels[::-1], fontsize=7)
    ax.set_xlabel(f"Times this segue occurred ({style.tier_short(comp)})")
    ax.set_title(f"Most frequent segues — top {len(top_edges)} of {n_segues} markers")
    # Value labels at the bar ends for exact counts.
    for bar, c in zip(bars, counts[::-1]):
        ax.annotate(
            f"{c:,}",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            va="center",
            fontsize=6,
            color="#374151",
        )
    ax.margins(x=0.12)
    ax.grid(axis="x", alpha=0.25)
    return True


def draw_era_density(ax: Axes, comp: Compendium) -> bool:
    density = eras.year_month_density(comp)
    if not density:
        return _draw_empty_panel(
            ax,
            "No year×month density in compendium.",
            title="Show density: year × month",
        )
    years = sorted({y for y, _m in density.keys()})
    grid = np.zeros((len(years), 12), dtype=np.int64)
    for (y, m), c in density.items():
        grid[years.index(y), m - 1] = c
    im = ax.imshow(grid, cmap="cividis", aspect="auto")
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="shows / month")
    ax.set_xticks(range(12))
    ax.set_xticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
    ax.set_yticks(range(len(years)))
    ax.set_yticklabels([str(y) for y in years])
    ax.set_title(f"Show density: year × month — {style.tier_short(comp)}")
    return True


def draw_personnel_gantt(ax: Axes, comp: Compendium) -> bool:
    bars = personnel_timeline.bars(comp)
    if not bars:
        return _draw_empty_panel(
            ax,
            "No personnel intervals in compendium.",
            title="Personnel timeline (Gantt)",
        )
    people = sorted({b.person_slug for b in bars})
    person_y = {p: i for i, p in enumerate(people)}
    cmap = plt.get_cmap("tab20")
    for b in bars:
        start_num = mdates.date2num(b.start)
        end_num = mdates.date2num(b.end or style.PERSONNEL_END_DEFAULT)
        ax.barh(
            person_y[b.person_slug],
            end_num - start_num,
            left=start_num,
            height=0.7,
            color=cmap(person_y[b.person_slug] % 20),
        )
    ax.set_yticks(list(person_y.values()))
    ax.set_yticklabels(people)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("Personnel timeline (Gantt)")
    return True


def draw_sentiment_by_kind(ax: Axes, comp: Compendium) -> bool:
    by_kind = reviews.sentiment_by_kind(comp)
    if not by_kind:
        return _draw_empty_panel(
            ax,
            "No review sentiment aggregates.",
            title=style.overlay_phrase(
                "Review sentiment by source kind", count=len(comp.reviews)
            ),
        )
    kinds = list(by_kind.keys())
    vals = [by_kind[k] for k in kinds]
    ax.bar(kinds, vals, color=style.COLORS["amber"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean sentiment")
    ax.set_title(
        style.overlay_phrase("Review sentiment by source kind", count=len(comp.reviews))
    )
    return True


def _draw_labeled_category_bars(
    ax: Axes, counter: Counter, *, title: str, xlabel: str, color: str
) -> bool:
    """Shared ranked horizontal-bar panel for categorical counts.

    Replaces low-information pie charts: bars are sorted by count, annotated
    with count and share-of-total, and use a single colorblind-safe hue (length,
    not colour, is the encoding).
    """
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    labels = [str(k) for k, _v in items]
    values = [v for _k, v in items]
    total = sum(values) or 1
    bars = ax.barh(list(range(len(items)))[::-1], values[::-1], color=color)
    ax.set_yticks(list(range(len(items)))[::-1])
    ax.set_yticklabels(labels[::-1], fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    for bar, v in zip(bars, values[::-1]):
        ax.annotate(
            f"{v:,} ({100 * v / total:.0f}%)",
            (bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            va="center",
            fontsize=7,
            color="#374151",
        )
    ax.margins(x=0.18)
    ax.grid(axis="x", alpha=0.25)
    return True


def draw_citation_kinds_pie(ax: Axes, comp: Compendium) -> bool:
    citation_kinds = Counter(c.kind for c in comp.citations)
    if not citation_kinds:
        return _draw_empty_panel(
            ax, "No citations in compendium.", title="Citation kinds"
        )
    return _draw_labeled_category_bars(
        ax,
        citation_kinds,
        title=f"Citation kinds (n={len(comp.citations)})",
        xlabel="Citations",
        color=style.COLORS["indigo"],
    )


def draw_recording_sources_pie(ax: Axes, comp: Compendium) -> bool:
    src_counter = Counter(r.source_type for r in comp.recordings)
    if not src_counter:
        return _draw_empty_panel(
            ax, "No recordings in compendium.", title="Recording source types"
        )
    return _draw_labeled_category_bars(
        ax,
        src_counter,
        title=f"Recording source types (n={len(comp.recordings)})",
        xlabel="Recordings",
        color=style.COLORS["sky"],
    )


def draw_shows_by_era(ax: Axes, comp: Compendium) -> None:
    era_counts = eras.shows_by_era(comp)
    ax.bar(
        list(era_counts.keys()), list(era_counts.values()), color=style.COLORS["purple"]
    )
    ax.set_ylabel(f"Shows ({style.tier_short(comp)})")
    ax.set_title("Shows by era")
    ax.tick_params(axis="x", rotation=20)


def draw_lyric_themes(ax: Axes, comp: Compendium, *, top_n: int = 20) -> bool:
    freq = lyrics.theme_frequencies(comp)
    if not freq:
        return _draw_empty_panel(
            ax,
            "No theme tags on lyric pointers.",
            title=style.overlay_phrase(
                "Top lyric themes", count=len(comp.lyric_pointers)
            ),
        )
    top_themes = list(freq.items())[:top_n]
    labels = [k for k, _ in top_themes]
    counts = [v for _, v in top_themes]
    ax.barh(labels[::-1], counts[::-1], color=style.COLORS["pink"])
    ax.set_xlabel("Frequency (theme occurrences)")
    ax.set_title(
        style.overlay_phrase("Top lyric themes", count=len(comp.lyric_pointers))
    )
    return True


def draw_lineup_diversity(ax: Axes, comp: Compendium) -> bool:
    diversity = personnel_timeline.lineup_diversity(comp)
    if not diversity:
        return _draw_empty_panel(
            ax, "No lineup diversity series.", title="Active lineup size over time"
        )
    # matplotlib accepts date objects on a date axis at runtime; the stubs do not
    # model this, so the x sequence is bound to Any to keep the annotation honest.
    dates: Any = [_date.fromisoformat(d) for d in diversity.keys()]
    sizes = list(diversity.values())
    ax.plot(
        dates, sizes, marker="o", linestyle="-", color=style.COLORS["sky"], markersize=3
    )
    ax.set_ylabel("Active members on show date")
    ax.set_ylim(0, max(sizes) + 1)
    ax.set_title("Active lineup size over time")
    return True


def draw_geo_scatter(ax: Axes, comp: Compendium, geo_map: dict | None = None) -> bool:
    geo_map = geo_map if geo_map is not None else geo.load_geo()
    if not geo_map:
        return _draw_empty_panel(ax, "No venue geo sidecar.", title="Venues (geocoded)")
    slugs = list({s.venue_slug for s in comp.shows} & set(geo_map.keys()))
    show_counts = Counter(s.venue_slug for s in comp.shows)
    lats = [float(geo_map[v]["lat"]) for v in slugs]
    lons = [float(geo_map[v]["lon"]) for v in slugs]
    regions = [str(geo_map[v]["region"]) for v in slugs]
    sizes = [12 + 12 * show_counts[v] for v in slugs]
    colors = [style.REGION_PALETTE.get(r, "#888") for r in regions]
    ax.scatter(
        lons, lats, s=sizes, c=colors, alpha=0.75, edgecolors="white", linewidth=0.5
    )
    # Label only the busiest venues — annotating all 900+ at archival scale is an
    # unreadable pile; size/color still encode every point.
    label_cap = 15
    busiest = {v for v, _ in show_counts.most_common(label_cap)}
    for v, lon, lat in zip(slugs, lons, lats):
        if v not in busiest:
            continue
        ax.annotate(
            v.split("_")[0],
            (lon, lat),
            fontsize=6,
            ha="center",
            xytext=(0, 6),
            textcoords="offset points",
        )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        f"Venues (size ∝ shows, n={len(slugs)} with geo; top {label_cap} labelled)"
    )
    ax.grid(True, alpha=0.2)
    from matplotlib.patches import Patch

    ax.legend(
        handles=[Patch(color=v, label=k) for k, v in style.REGION_PALETTE.items()],
        loc="lower left",
    )
    return True


def draw_set_positions(ax: Axes, comp: Compendium) -> bool:
    dist = positions.position_distribution(comp)
    if not dist:
        return _draw_empty_panel(
            ax, "No set-position distribution.", title="Set-position distribution"
        )
    ax.bar(list(dist.keys()), list(dist.values()), color=style.COLORS["indigo"])
    ax.set_xlabel("Position within set")
    ax.set_ylabel("Performance count")
    ax.set_title("Set-position distribution")
    return True


def draw_stationary_top(ax: Axes, comp: Compendium, *, top_n: int = 20) -> bool:
    tm = transitions.fit(comp, exclude_segments=True)
    sd = stationary.compute(tm)
    if not sd:
        return _draw_empty_panel(
            ax,
            "Markov model empty.",
            title=f"Markov stationary distribution — top {top_n}",
        )
    top = sorted(sd.items(), key=lambda kv: -kv[1])[:top_n]
    labels, vals = zip(*top)
    pretty_labels = [_pretty(slug) for slug in labels]
    ax.barh(pretty_labels[::-1], list(vals)[::-1], color=style.COLORS["sky"])
    ax.set_xlabel("Stationary probability")
    ax.set_title(f"Markov stationary distribution — top {top_n}; segments excluded")
    return True


def draw_centrality_top(ax: Axes, comp: Compendium, *, top_n: int = 20) -> bool:
    songs, m = cooccurrence.cooccurrence_matrix(comp, exclude_segments=True)
    # Centrality on the Jaccard-association adjacency, not raw counts: this
    # measures bridging importance independent of raw play frequency (raw
    # counts would just re-derive frequency — see analysis/centrality.py).
    ec = centrality.eigenvector_centrality(songs, cooccurrence.jaccard_matrix(m))
    if not ec:
        return _draw_empty_panel(
            ax,
            "Co-occurrence graph empty.",
            title=f"Association centrality — top {top_n}",
        )
    top = sorted(ec.items(), key=lambda kv: -kv[1])[:top_n]
    labels, vals = zip(*top)
    pretty_labels = [_pretty(slug) for slug in labels]
    ax.barh(pretty_labels[::-1], list(vals)[::-1], color=style.COLORS["lime"])
    ax.set_xlabel("Eigenvector centrality (Jaccard association)")
    ax.set_title(f"Association centrality — top {top_n}; segments excluded")
    return True


def draw_releases_timeline(ax: Axes, comp: Compendium) -> bool:
    if not comp.releases:
        return _draw_empty_panel(
            ax, "No releases in compendium.", title="Releases timeline (by kind)"
        )
    kinds = sorted({r.kind for r in comp.releases})
    kind_y = {k: i for i, k in enumerate(kinds)}
    cmap = plt.get_cmap("Set1")
    # List only the most recent releases in a compact inset. Direct point
    # annotations collide at archival scale because many recent releases share
    # the same kind row and similar dates.
    label_cap = 6
    recent = sorted(comp.releases, key=lambda r: r.release_date, reverse=True)[
        :label_cap
    ]
    for r in comp.releases:
        # date x-coordinate is valid for matplotlib at runtime; stubs are too narrow,
        # so the date is bound to Any rather than suppressed per-line.
        x_date: Any = r.release_date
        ax.scatter(
            x_date,
            kind_y[r.kind],
            s=42,
            color=cmap(kind_y[r.kind]),
            edgecolors="white",
        )
    if recent:
        lines = ["Most recent releases"] + [
            f"{r.release_date.year}  {shorten(r.title, width=34, placeholder='...')}"
            for r in recent
        ]
        ax.text(
            0.985,
            0.08,
            "\n".join(lines),
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=7,
            color="#111827",
            linespacing=1.2,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "#d1d5db",
                "alpha": 0.92,
            },
        )
    ax.set_yticks(list(kind_y.values()))
    ax.set_yticklabels(kinds)
    n_rel = len(comp.releases)
    suffix = f"; most recent {label_cap} listed" if n_rel > label_cap else ""
    ax.set_title(f"Releases timeline (by kind, n={n_rel}{suffix})")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.margins(x=0.08, y=0.18)
    return True


def draw_tours_top(ax: Axes, comp: Compendium, *, top_n: int = 15) -> bool:
    pt = tours.shows_per_tour(comp)
    if not pt:
        return _draw_empty_panel(
            ax,
            "No tour labels on shows (ingest uses untagged bucket).",
            title=f"Top tours — {style.tier_phrase(comp)}",
        )
    top = list(pt.items())[:top_n]
    labels, vals = zip(*top)
    ax.barh(list(labels)[::-1], list(vals)[::-1], color=style.COLORS["violet"])
    ax.set_xlabel(f"Shows ({style.tier_short(comp)})")
    ax.set_title(f"Top tours — {style.tier_phrase(comp)}")
    return True


def draw_bustouts(ax: Axes, comp: Compendium, *, top_n: int = 15) -> bool:
    """Songs with the widest recurrence gap (returns after long absence)."""
    top = bustouts.biggest_bustouts(comp, top_n=top_n)
    if not top or top[0].max_gap_shows == 0:
        return _draw_empty_panel(
            ax,
            "No recurrence gaps in compendium.",
            title=f"Widest recurrence gaps — top {top_n}",
        )
    labels = [g.song_slug for g in top]
    pretty_labels = [_pretty(slug) for slug in labels]
    gaps = [g.max_gap_shows for g in top]
    ax.barh(pretty_labels[::-1], gaps[::-1], color=style.COLORS["amber"])
    ax.set_xlabel(f"Max intervening shows between plays ({style.tier_short(comp)})")
    ax.set_title(f"Widest recurrence gaps — top {top_n}")
    return True


def draw_song_lifespans(ax: Axes, comp: Compendium, *, top_n: int = 25) -> bool:
    """Lollipop range bars: first→last performance year of top songs by debut.

    Each song is a horizontal segment from its debut year to its last-played
    year (a span line with endpoint markers), ordered by debut, colored by
    debut era — the "when did this enter and leave rotation" view of the
    repertoire. Segment markers are excluded.
    """
    spans = repertoire.song_lifespans(comp, top_n=top_n)
    if not spans:
        return _draw_empty_panel(
            ax, "No song lifespans in compendium.", title="Song lifespans"
        )
    era_names = [name for name, _s, _e in eras.ERAS]
    era_color = {
        name: plt.get_cmap("tab10")(i % 10) for i, name in enumerate(era_names)
    }
    labels = [_pretty(ls.song_slug) for ls in spans]
    y = list(range(len(spans)))
    for yi, ls in zip(y, spans):
        color = era_color.get(ls.debut_era, "#9ca3af")
        ax.plot(
            [ls.first_year, ls.last_year], [yi, yi], "-", color=color, linewidth=1.5
        )
        ax.plot([ls.first_year, ls.last_year], [yi, yi], "o", color=color, markersize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlabel(f"Year first → last performed ({style.tier_short(comp)})")
    ax.set_title(f"Song lifespans — top {top_n} by performances, ordered by debut")
    ax.invert_yaxis()
    return True


def categorical_summary(comp: Compendium) -> dict[str, bool]:
    f_set = setlist_functor(comp)
    f_lin = lineup_functor(comp)
    p_active = active_lineup_presheaf(comp)
    return {
        "setlist_functor_monotone": is_monotone(f_set),
        "lineup_functor_monotone": is_monotone(f_lin),
        "active_lineup_presheaf_expected_non_monotone": not is_monotone(p_active),
        "cardinality_eta_naturality_holds": naturality_square_holds(f_set),
    }


def categorical_summary_text(comp: Compendium) -> str:
    c = categorical_summary(comp)
    return (
        f"Covariant functors monotone: setlist={c['setlist_functor_monotone']}, "
        f"lineup={c['lineup_functor_monotone']}; "
        f"active presheaf (expected non-monotone): "
        f"{c['active_lineup_presheaf_expected_non_monotone']}; "
        f"cardinality-η naturality square holds="
        f"{c['cardinality_eta_naturality_holds']}."
    )


def draw_functor_cardinalities_with_presheaf(ax: Axes, comp: Compendium) -> None:
    f_set = setlist_functor(comp)
    f_lin = lineup_functor(comp)
    p_active = active_lineup_presheaf(comp)
    f_dates = sorted(f_set.keys())
    f_sizes = [len(f_set[d]) for d in f_dates]
    l_sizes = [len(f_lin[d]) for d in f_dates]
    p_sizes = [len(p_active[d]) for d in f_dates]
    ax.plot(
        range(len(f_dates)),
        f_sizes,
        label="|F_setlist|",
        color=style.COLORS["purple"],
        lw=1.5,
    )
    ax.plot(
        range(len(f_dates)),
        l_sizes,
        label="|F_lineup| (cumulative)",
        color=style.COLORS["amber"],
        lw=1.5,
    )
    ax.plot(
        range(len(f_dates)),
        p_sizes,
        label="|P_active| (presheaf)",
        color=style.COLORS["green"],
        lw=1.2,
        linestyle="--",
    )
    ax.legend(fontsize=8)
    ax.set_title("Cumulative functor cardinalities + active-roster presheaf")
    ax.set_xlabel("Show index (chronological)")
