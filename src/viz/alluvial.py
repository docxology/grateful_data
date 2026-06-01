"""Three-column alluvial: composer → song → era flow diagram."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from ..analysis import eras
from ..integration.reconcile import Compendium
from . import panels
from .figures import ALLUVIAL_FILENAME, ALLUVIAL_TOP_PATHS


def build_alluvial(comp: Compendium) -> Figure:
    show_to_era = {s.slug: eras.era_of(s.date) for s in comp.shows}
    song_to_composers = {s.slug: tuple(s.composers) for s in comp.songs}

    flow: Counter[tuple[str, str, str]] = Counter()
    for p in comp.performances:
        era = show_to_era.get(p.show_slug, "Unknown")
        for c in song_to_composers.get(p.song_slug, ()):
            flow[(c, p.song_slug, era)] += 1

    if not flow:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "No composer→song→era flow paths in compendium.",
            ha="center",
            va="center",
            fontsize=11,
            color="#6b7280",
        )
        ax.set_title("Composer → song → era flow")
        return fig

    top = flow.most_common(ALLUVIAL_TOP_PATHS)
    eras_set = [
        "Primal",
        "Europe 72",
        "Wall of Sound",
        "Hiatus->Return",
        "Brent",
        "Vince+Bruce",
    ]

    def positions(
        items: list[str], totals: dict[str, int]
    ) -> dict[str, tuple[float, float]]:
        out: dict[str, tuple[float, float]] = {}
        total_h = sum(totals.values()) or 1
        cursor = 0.0
        for item in items:
            h = totals[item] / total_h
            out[item] = (cursor, cursor + h)
            cursor += h + 0.005
        return out

    composer_totals: dict[str, int] = defaultdict(int)
    song_totals: dict[str, int] = defaultdict(int)
    era_totals: dict[str, int] = defaultdict(int)
    for (c, s, e), v in top:
        composer_totals[c] += v
        song_totals[s] += v
        era_totals[e] += v

    composers = sorted(composer_totals, key=lambda c: (-composer_totals[c], c))
    songs = sorted(song_totals, key=lambda s: (-song_totals[s], s))
    cp = positions(composers, composer_totals)
    sp = positions(songs, song_totals)
    ep = positions([e for e in eras_set if e in era_totals], era_totals)

    fig, ax = plt.subplots(figsize=(11, max(6, len(songs) * 0.18)))
    ax.set_xlim(-0.02, 3.28)
    ax.set_ylim(0, 1.18)
    ax.axis("off")
    cmap = plt.get_cmap("tab20")

    def draw_column(
        positions_map: dict[str, tuple[float, float]],
        x: float,
        color_offset: int,
        fontsize: int,
    ) -> None:
        for i, (label, (a, b)) in enumerate(positions_map.items()):
            ax.add_patch(
                mpatches.Rectangle(
                    (x, a), 0.05, b - a, color=cmap((i + color_offset) % 20)
                )
            )
            display = (
                panels._pretty(label) if ("_" in label or label.islower()) else label
            )
            ax.text(
                x + 0.06,
                (a + b) / 2,
                display,
                fontsize=fontsize,
                va="center",
                ha="left",
                clip_on=False,
            )

    draw_column(cp, 0.0, 0, 8)
    draw_column(sp, 1.5, 7, 7)
    draw_column(ep, 3.0 - 0.05, 14, 8)

    composer_cursor = {c: cp[c][0] for c in cp}
    song_in_cursor = {s: sp[s][0] for s in sp}
    era_cursor = {e: ep[e][0] for e in ep}

    for (c, s, e), v in top:
        if c not in cp or s not in sp or e not in ep:
            continue
        total = sum(vv for (cc, ss, _ee), vv in top if cc == c) or 1
        h = (cp[c][1] - cp[c][0]) * (v / total)
        a1, b1 = composer_cursor[c], composer_cursor[c] + h
        composer_cursor[c] = b1
        h2 = (sp[s][1] - sp[s][0]) * (
            v / (sum(vv for (_cc, ss, _ee), vv in top if ss == s) or 1)
        )
        a2, b2 = song_in_cursor[s], song_in_cursor[s] + h2
        song_in_cursor[s] = b2
        verts = [
            (0.05, a1),
            (0.8, a1),
            (0.8, a2),
            (1.5, a2),
            (1.5, b2),
            (0.8, b2),
            (0.8, b1),
            (0.05, b1),
        ]
        ax.add_patch(
            mpatches.Polygon(
                verts, closed=True, alpha=0.35, color=cmap(composers.index(c) % 20)
            )
        )

    song_out_cursor = {s: sp[s][0] for s in sp}
    for (_c, s, e), v in top:
        if s not in sp or e not in ep:
            continue
        total = sum(vv for (_cc, ss, _ee), vv in top if ss == s) or 1
        h2 = (sp[s][1] - sp[s][0]) * (v / total)
        a2, b2 = song_out_cursor[s], song_out_cursor[s] + h2
        song_out_cursor[s] = b2
        h3 = (ep[e][1] - ep[e][0]) * (
            v / (sum(vv for (_cc, _ss, ee), vv in top if ee == e) or 1)
        )
        a3, b3 = era_cursor[e], era_cursor[e] + h3
        era_cursor[e] = b3
        verts = [
            (1.55, a2),
            (2.3, a2),
            (2.3, a3),
            (2.95, a3),
            (2.95, b3),
            (2.3, b3),
            (2.3, b2),
            (1.55, b2),
        ]
        ax.add_patch(
            mpatches.Polygon(
                verts, closed=True, alpha=0.35, color=cmap((songs.index(s) + 7) % 20)
            )
        )

    ax.set_title(
        f"Composer → song → era flow (top {ALLUVIAL_TOP_PATHS} paths, ribbon width ∝ performances)",
        pad=24,
    )
    fig.subplots_adjust(left=0.03, right=0.97, top=0.88, bottom=0.06)
    return fig


def save_alluvial(comp: Compendium, path: Path) -> Path:
    fig = build_alluvial(comp)
    path = path if path.name else path / ALLUVIAL_FILENAME
    return panels.save_figure(fig, path, dpi=160, comp=comp)
