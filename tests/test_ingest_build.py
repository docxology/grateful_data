"""Build orchestration tests (fixture vendor, no network mocks)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ingest.build import (
    build_archival_compendium,
    ensure_gdshowsdb_vendor,
    write_archival_snapshot,
)
from src.ingest.merge_sources import (
    MergeInputs,
    merge_archival,
    _merge_gap_shows,
    _merge_people,
)
from src.models import Performance, Show, canonical_show_id
from datetime import date

FIXTURE_VENDOR = (
    Path(__file__).resolve().parent / "fixtures" / "ingest" / "gdshowsdb_mini"
)
SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"


def test_ensure_gdshowsdb_vendor_offline_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("src.ingest.build.VENDOR_DIR", tmp_path / "missing")
    with pytest.raises(FileNotFoundError, match="gdshowsdb vendor not found"):
        ensure_gdshowsdb_vendor(online=False)


def test_ensure_gdshowsdb_vendor_uses_fixture(monkeypatch):
    monkeypatch.setattr("src.ingest.build.VENDOR_DIR", FIXTURE_VENDOR)
    assert ensure_gdshowsdb_vendor(online=False) == FIXTURE_VENDOR


def test_build_archival_compendium_offline(monkeypatch):
    monkeypatch.setattr("src.ingest.build.VENDOR_DIR", FIXTURE_VENDOR)
    comp, report = build_archival_compendium(online=False)
    assert report.entity_counts["shows"] >= 2
    assert len(comp.performances) >= 2
    assert "gdshowsdb" in report.sources_used


def test_write_archival_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr("src.ingest.build.VENDOR_DIR", FIXTURE_VENDOR)
    comp, report = build_archival_compendium(online=False)
    out = tmp_path / "archival"
    monkeypatch.setattr("src.ingest.build.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr("src.ingest.build.SEED_DIR", SEED_DIR)
    path = write_archival_snapshot(comp, report, out_dir=out)
    assert path == out
    assert (out / "shows.json").is_file()
    build_report = json.loads(
        (tmp_path / "output" / "archival" / "build_report.json").read_text()
    )
    assert build_report["entity_counts"]["shows"] >= 2


def test_merge_gap_shows_appends_missing():
    primary_show = Show(
        slug=canonical_show_id(date(1977, 5, 8), "barton_hall"),
        date=date(1977, 5, 8),
        venue_slug="barton_hall",
    )
    extra_show = Show(
        slug=canonical_show_id(date(1972, 8, 27), "oregon_state"),
        date=date(1972, 8, 27),
        venue_slug="oregon_state",
    )
    primary_perfs = [
        Performance(
            show_slug=primary_show.slug,
            song_slug="scarlet_begonias",
            set_number=1,
            position=1,
        )
    ]
    extra_perfs = [
        Performance(
            show_slug=extra_show.slug,
            song_slug="china_cat_sunflower",
            set_number=1,
            position=1,
            segue_into="i_know_you_rider",
        )
    ]
    shows = [primary_show]
    perfs = list(primary_perfs)
    _merge_gap_shows(shows, perfs, [extra_show], extra_perfs)
    assert len(shows) == 2
    assert any(p.segue_into for p in perfs)


def test_merge_people_dedupes_by_name():
    from src.models import Person

    curated = [Person(slug="garcia", full_name="Jerome John Garcia", intervals=())]
    extra = [Person(slug="jerry_garcia", full_name="Jerome John Garcia", intervals=())]
    _merge_people(curated, extra)
    assert len(curated) == 1


def test_merge_archival_online_with_vendor_fixtures(monkeypatch, tmp_path):
    vendor_root = tmp_path / "vendor"
    (vendor_root / "cmu").mkdir(parents=True)
    (vendor_root / "whitegum").mkdir(parents=True)
    (vendor_root / "dead_net").mkdir(parents=True)
    (vendor_root / "wikipedia").mkdir(parents=True)
    fixtures = Path(__file__).resolve().parent / "fixtures" / "ingest"
    (vendor_root / "cmu" / "gs.html").write_text(
        (fixtures / "cmu_mini.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (vendor_root / "cmu" / "dead-lyrics.html").write_text(
        (fixtures / "cmu_lyrics_mini.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (vendor_root / "maximinus").mkdir(parents=True, exist_ok=True)
    (vendor_root / "maximinus" / "dead_reviews.txt").write_text(
        (fixtures / "maximinus_mini.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (vendor_root / "whitegum" / "intro.htm").write_text(
        (fixtures / "whitegum_mini.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (vendor_root / "dead_net" / "band.html").write_text(
        (fixtures / "dead_net_mini.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (vendor_root / "dead_net" / "songs.html").write_text(
        "<html><body>" + '<a href="/song/ripple">Ripple</a>' * 80 + "</body></html>",
        encoding="utf-8",
    )
    (vendor_root / "wikipedia" / "discography.json").write_text(
        json.dumps(
            [
                {
                    "title": "American Beauty",
                    "release_date": "1970-11-01",
                    "kind": "studio",
                }
            ]
        ),
        encoding="utf-8",
    )
    (vendor_root / "wikipedia" / "members.json").write_text(
        (fixtures / "wikipedia_members.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "src.ingest._vendor_fetch.VENDOR_ROOT",
        vendor_root,
    )
    monkeypatch.setattr(
        "src.ingest.fetch_internet_archive.fetch_lma_recordings",
        lambda max_rows=0: (),
    )
    from src.ingest.gdshowsdb_yaml import load_gdshowsdb_vendor

    dump = load_gdshowsdb_vendor(FIXTURE_VENDOR)
    comp, report = merge_archival(
        MergeInputs(
            gdshows_dump=dump,
            curated_seed_dir=SEED_DIR,
            online=True,
            ia_max_rows=0,
            skip_truckin=True,
        )
    )
    assert any("cmu_leone_setlists" in s for s in report.sources_used)
    assert "whitegum_alex_allan" in report.sources_used
    assert "wikipedia_gd" in report.sources_used
    assert "internet_archive_lma" in report.sources_used
    assert "bibliography_combined" in report.sources_used
    assert "maximinus_reviews" in report.sources_used
    assert any("cmu_leone_lyrics" in s for s in report.sources_used)
    assert any(s for s in report.skipped if s.startswith("setlistfm_gd"))
    assert any(s for s in report.skipped if s.startswith("gratefulstats_api"))
    assert report.ingest_stats.get("dead_net_song_links", 0) >= 1
    assert len(comp.shows) >= 2
