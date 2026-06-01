"""Tests for the figure registry SSOT."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

from src.viz.figures import (
    DASHBOARD_FIGURES,
    EXPECTED_FILENAMES,
    FIGURE_SPECS,
    render_all_panels,
    render_group,
    render_one,
    specs_for_group,
)


def test_expected_filenames_match_panel_specs_plus_composites():
    panel_names = {spec.filename for spec in FIGURE_SPECS}
    assert len(panel_names) == len(FIGURE_SPECS)
    assert set(EXPECTED_FILENAMES) == panel_names | {
        "mosaic.png",
        "alluvial_composer_song_era.png",
    }


def test_dashboard_figures_include_mosaic_and_all_panel_specs():
    assert DASHBOARD_FIGURES[0] == "mosaic.png"
    assert set(DASHBOARD_FIGURES[1:]) == {
        spec.filename for spec in FIGURE_SPECS if spec.dashboard
    }


def test_every_figure_spec_has_dashboard_metadata():
    for spec in FIGURE_SPECS:
        assert spec.display_title
        assert spec.alt_text
        assert spec.alt_text != spec.display_title
        assert spec.caption_hint
        assert spec.data_source
        assert spec.statistic
        assert spec.exclusion_rule
        assert "Registered compendium/report" not in spec.data_source
        assert "Figure-specific statistic" not in spec.statistic
        assert "Loaded-tier scope" not in spec.exclusion_rule
        assert spec.claim_class in {"descriptive", "exploratory", "validation"}
        assert spec.dataset is not None or spec.dataset_reason


def test_every_spec_renders_on_compendium(tmp_path, compendium):
    for spec in FIGURE_SPECS:
        path = render_one(spec, compendium, tmp_path)
        if path is not None:
            assert path.exists()
            assert path.stat().st_size > 0


def test_render_group_core(tmp_path, compendium):
    paths = render_group(compendium, tmp_path, "core")
    assert len(paths) == 5
    assert all(p.name.endswith(".png") for p in paths)


def test_specs_for_group_and_render_all_panels(tmp_path, compendium):
    assert len(specs_for_group("extended")) == 10
    assert len(specs_for_group("more")) == 19
    paths = render_all_panels(compendium, tmp_path / "all")
    assert len(paths) == len(FIGURE_SPECS)
    assert all(p.stat().st_size > 0 for p in paths)
