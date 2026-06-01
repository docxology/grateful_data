"""Tests for figure validation, including a blank-image negative control."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

from src.viz import panels, style
from src.viz.validate import validate_figure, validate_figures


def _real_figure(tmp_path, compendium):
    fig, ax = plt.subplots(figsize=(6, 4))
    panels.draw_top_songs(ax, compendium)
    return panels.save_figure(fig, tmp_path / "top_songs.png")


def test_real_figure_passes(tmp_path, compendium):
    path = _real_figure(tmp_path, compendium)
    result = validate_figure(path)
    assert result.ok, result.reasons
    assert result.exists
    assert result.width >= 100 and result.height >= 100
    assert result.pixel_variance > 0


def test_missing_file_fails(tmp_path):
    result = validate_figure(tmp_path / "does_not_exist.png")
    assert not result.ok
    assert not result.exists
    assert "does not exist" in result.reasons[0]


def test_blank_image_is_rejected(tmp_path):
    """Negative control: a uniform (blank) canvas must fail validation."""
    blank = tmp_path / "blank.png"
    mpimg.imsave(str(blank), np.ones((200, 200, 3)))
    # min_bytes=1 isolates the variance check from the size check.
    result = validate_figure(blank, min_bytes=1)
    assert not result.ok
    assert any("blank" in r for r in result.reasons)


def test_tiny_image_fails_dimension(tmp_path):
    tiny = tmp_path / "tiny.png"
    mpimg.imsave(str(tiny), np.random.default_rng(0).random((10, 10, 3)))
    result = validate_figure(tiny, min_bytes=1)
    assert not result.ok
    assert any("dimensions too small" in r for r in result.reasons)


def test_validate_figures_flags_missing(tmp_path, compendium):
    _real_figure(tmp_path, compendium)
    report = validate_figures(tmp_path, expected=["top_songs.png", "absent.png"])
    assert "absent.png" in report.missing
    assert not report.all_ok
    assert report.n_ok == 1


def test_validate_figures_all_ok_without_expected(tmp_path, compendium):
    _real_figure(tmp_path, compendium)
    report = validate_figures(tmp_path)
    assert report.all_ok
    assert report.to_dict()["n_figures"] == 1


def test_provenance_text_is_honest(compendium):
    text = style.provenance_text(compendium)
    assert "curated real shows" in text
    assert str(len(compendium.shows)) in text


def test_figure_with_provenance_still_validates(tmp_path, compendium):
    """ISC-16: an improved (footer-stamped) figure renders and validates."""
    fig, ax = plt.subplots(figsize=(6, 4))
    panels.draw_top_songs(ax, compendium)
    fig.tight_layout()
    style.add_provenance(fig, compendium)
    # the footer text is present among the figure's text artists
    assert any("curated real shows" in t.get_text() for t in fig.texts)
    path = panels.save_figure(fig, tmp_path / "with_footer.png")
    assert validate_figure(path).ok
