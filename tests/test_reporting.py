"""Tests for reporting modules (dashboard, entity pages, song pages)."""

from __future__ import annotations

from src.reporting.dashboard import build_dashboard_html
from src.reporting.entity_pages import write_entity_pages
from src.reporting.song_pages import write_song_pages
from src.viz.alluvial import build_alluvial, save_alluvial


def test_build_dashboard_html_includes_kpis(compendium):
    html = build_dashboard_html(compendium)
    assert "The Music Never Stopped" in html
    assert str(len(compendium.shows)) in html
    assert "figures/mosaic.png" in html
    assert "Most-Performed Songs" in html
    assert "Yearly bars count shows" in html
    assert "Statistic" in html
    assert "Exclusion" in html
    assert "First-Principles Review" in html
    assert "Claim ledger" in html
    assert "audited-descriptive" in html


def test_dashboard_links_raw_figure_data(tmp_path, compendium):
    figures_dir = tmp_path / "figures"
    data_dir = tmp_path / "data" / "figures"
    figures_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    (figures_dir / "top_songs.png").write_bytes(b"png")
    (figures_dir / "claim_evidence_matrix.png").write_bytes(b"png")
    (data_dir / "top_songs.csv").write_text("rank,song\n", encoding="utf-8")
    (data_dir / "top_songs.json").write_text("{}", encoding="utf-8")
    (data_dir / "claim_evidence_matrix.csv").write_text(
        "claim_class,artifact_family,n_claim_families\n", encoding="utf-8"
    )
    (data_dir / "claim_evidence_matrix.json").write_text("{}", encoding="utf-8")
    html = build_dashboard_html(compendium, figures_dir=figures_dir, data_dir=data_dir)
    assert "data/figures/top_songs.csv" in html
    assert "data/figures/top_songs.json" in html
    assert "data/figures/claim_evidence_matrix.csv" in html


def test_write_song_pages_creates_index(tmp_path, compendium):
    index = write_song_pages(compendium, tmp_path / "songs")
    assert index.exists()
    assert index.name == "_index.md"
    assert len(list((tmp_path / "songs").glob("*.md"))) == len(compendium.songs) + 1


def test_write_entity_pages_creates_three_indexes(tmp_path, compendium):
    era_dir, venue_dir, person_dir = write_entity_pages(compendium, tmp_path)
    assert (era_dir / "_index.md").exists()
    assert (venue_dir / "_index.md").exists()
    assert (person_dir / "_index.md").exists()


def test_alluvial_builds_figure(compendium):
    fig = build_alluvial(compendium)
    assert fig is not None


def test_save_alluvial_writes_png(tmp_path, compendium):
    path = save_alluvial(compendium, tmp_path / "alluvial_composer_song_era.png")
    assert path is not None
    assert path.exists()
    assert path.stat().st_size > 0
