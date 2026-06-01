"""Negative-control test for the alluvial empty-state branch.

Covers the path where a compendium yields no composer→song→era flow paths, so
``build_alluvial`` must still return a real, non-degenerate empty-state Figure
(never ``None``) — the property the ``-> Figure`` annotation promises.
"""

from __future__ import annotations

from matplotlib.figure import Figure

from src.integration.reconcile import Compendium
from src.viz.alluvial import build_alluvial


def _empty_compendium() -> Compendium:
    return Compendium(
        shows=(),
        venues=(),
        songs=(),
        people=(),
        performances=(),
        recordings=(),
        releases=(),
        citations=(),
        lyric_pointers=(),
        reviews=(),
    )


def test_build_alluvial_empty_returns_real_figure():
    fig = build_alluvial(_empty_compendium())
    assert isinstance(fig, Figure)
    # Empty-state panel is drawn with an explanatory message, not left blank.
    axes = fig.axes
    assert len(axes) == 1
    texts = [t.get_text() for t in axes[0].texts]
    assert any("No composer" in t for t in texts)
