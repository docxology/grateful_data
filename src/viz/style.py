"""Shared matplotlib styling for grateful_data figures."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from ..integration.reconcile import Compendium

FIG_DPI = 150
MOSAIC_DPI = 200
MOSAIC_FIGSIZE = (22, 34)

COLORS = {
    "blue": "#3B82F6",
    "red": "#EF4444",
    "green": "#10B981",
    "purple": "#8B5CF6",
    "amber": "#F59E0B",
    "pink": "#EC4899",
    "indigo": "#6366F1",
    "sky": "#0EA5E9",
    "lime": "#22c55e",
    "violet": "#A78BFA",
}

REGION_PALETTE = {
    "West": COLORS["blue"],
    "Northeast": COLORS["red"],
    "South": COLORS["green"],
    "Midwest": COLORS["amber"],
}

PERSONNEL_END_DEFAULT = __import__("datetime").date(1995, 8, 9)

TITLE_FONTSIZE = 11
LABEL_FONTSIZE = 9
TICK_FONTSIZE = 8


def style_axes(ax) -> None:
    """Light publication styling shared across panel figures."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=TICK_FONTSIZE)
    ax.title.set_fontsize(TITLE_FONTSIZE)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def resolve_tier() -> str:
    """Return ``seed`` or ``archival`` from env / resolved data directory."""
    import os

    from ..tier import resolve_seed_dir

    tier = os.environ.get("GRATEFUL_DATA_TIER", "").strip().lower()
    if tier in ("seed", "archival"):
        return tier
    return resolve_seed_dir().name


def tier_phrase(comp: Compendium) -> str:
    """Short honest label for figure titles."""
    tier = resolve_tier()
    n = len(comp.shows)
    if tier == "archival":
        return f"archival compendium (n={n} shows)"
    return f"seed compendium (n={n} shows)"


def tier_short(comp: Compendium) -> str:
    """One-word corpus label for axis annotations."""
    return "archival" if resolve_tier() == "archival" else "seed"


def overlay_phrase(entity: str, *, count: int) -> str:
    """Label curated dimensions that do not scale with gdshowsdb."""
    return f"{entity} (curated overlay, n={count})"


def provenance_text(comp: Compendium, *, tier: str | None = None) -> str:
    """Uniform, honest provenance label for every figure footer."""
    if tier is None:
        tier = resolve_tier()
    dates = sorted(s.date.isoformat() for s in comp.shows)
    span = f"{dates[0]} … {dates[-1]}" if dates else "n/a"
    if tier == "archival":
        label = "archival compendium"
        count_phrase = "ingested shows"
    else:
        label = "seed compendium"
        count_phrase = "curated real shows"
    return (
        f"{label} · n={len(comp.shows)} {count_phrase} · {span} · "
        "computed over audited bundled data"
    )


def add_provenance(fig: Figure, comp: Compendium, *, tier: str | None = None) -> Figure:
    """Stamp the shared provenance footer onto a figure (deterministic)."""
    if tier is None:
        tier = resolve_tier()
    fig.text(
        0.995,
        0.004,
        provenance_text(comp, tier=tier),
        ha="right",
        va="bottom",
        fontsize=6,
        color="#6b7280",
        alpha=0.9,
    )
    return fig
