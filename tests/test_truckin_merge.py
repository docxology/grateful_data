"""Tests for truckin-through-time gap-fill merge."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.ingest.fetch_truckin_db import ensure_truckin_db
from src.ingest.gdshowsdb_yaml import load_gdshowsdb_vendor
from src.ingest.merge_sources import MergeInputs, merge_archival

FIXTURE_VENDOR = (
    Path(__file__).resolve().parent / "fixtures" / "ingest" / "gdshowsdb_mini"
)
SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"


@pytest.fixture
def truckin_vendor_db(tmp_path: Path) -> Path:
    vendor_root = tmp_path / "vendor"
    (vendor_root / "truckin").mkdir(parents=True)
    db = vendor_root / "truckin" / "database.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE venue (id INTEGER PRIMARY KEY, name TEXT, city TEXT, state TEXT, country TEXT);
        CREATE TABLE song (id INTEGER PRIMARY KEY, title TEXT);
        CREATE TABLE concert (id INTEGER PRIMARY KEY, venue_id INTEGER, date TEXT);
        CREATE TABLE setlist (id INTEGER PRIMARY KEY, concert_id INTEGER, notes TEXT);
        CREATE TABLE setlistsong (id INTEGER PRIMARY KEY, setlist_id INTEGER, song_id INTEGER, "order" INTEGER, transition INTEGER);
        INSERT INTO venue VALUES (1, 'Fillmore West', 'San Francisco', 'CA', 'US');
        INSERT INTO song VALUES (1, 'Dark Star');
        INSERT INTO concert VALUES (1, 1, '1969-02-27');
        INSERT INTO setlist VALUES (1, 1, '');
        INSERT INTO setlistsong VALUES (1, 1, 1, 1, 0);
        """
    )
    conn.commit()
    conn.close()
    return vendor_root


def test_ensure_truckin_downloads_when_missing(tmp_path, httpserver, monkeypatch):
    db = tmp_path / "remote.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE venue (id INTEGER PRIMARY KEY, name TEXT, city TEXT, state TEXT, country TEXT);
        CREATE TABLE song (id INTEGER PRIMARY KEY, title TEXT);
        CREATE TABLE concert (id INTEGER PRIMARY KEY, venue_id INTEGER, date TEXT);
        CREATE TABLE setlist (id INTEGER PRIMARY KEY, concert_id INTEGER, notes TEXT);
        CREATE TABLE setlistsong (id INTEGER PRIMARY KEY, setlist_id INTEGER, song_id INTEGER, "order" INTEGER, transition INTEGER);
        """
    )
    conn.commit()
    conn.close()
    httpserver.expect_request("/database.db").respond_with_data(db.read_bytes())
    monkeypatch.setattr(
        "src.ingest.fetch_truckin_db.TRUCKIN_DB_URL",
        httpserver.url_for("/database.db"),
    )
    vendor_root = tmp_path / "vendor"
    monkeypatch.setattr("src.ingest._vendor_fetch.VENDOR_ROOT", vendor_root)
    path = ensure_truckin_db(online=True)
    assert path.is_file()


def test_truckin_gap_fill_merges(monkeypatch, truckin_vendor_db):
    monkeypatch.setattr("src.ingest._vendor_fetch.VENDOR_ROOT", truckin_vendor_db)
    monkeypatch.setattr(
        "src.ingest.fetch_internet_archive.fetch_lma_recordings",
        lambda max_rows=0: (),
    )
    dump = load_gdshowsdb_vendor(FIXTURE_VENDOR)
    comp, report = merge_archival(
        MergeInputs(
            gdshows_dump=dump,
            curated_seed_dir=SEED_DIR,
            online=True,
            skip_cmu=True,
            skip_whitegum=True,
            skip_wikipedia=True,
            skip_maximinus=True,
            skip_bibliography=True,
            skip_cmu_lyrics=True,
            skip_dead_net=True,
            skip_dead_net_songs=True,
            skip_gratefulstats=True,
        )
    )
    assert "truckin_through_time_sqlite" in report.sources_used
    assert report.ingest_stats.get("truckin_gap_shows", 0) >= 1
    assert len(comp.performances) >= 1


def test_merge_gratefulstats_probe(monkeypatch):
    from src.models import Citation

    monkeypatch.setattr(
        "src.ingest.fetch_internet_archive.fetch_lma_recordings",
        lambda max_rows=0: (),
    )
    monkeypatch.setenv("GRATEFULSTATS_API_KEY", "probe-token")
    monkeypatch.setattr(
        "src.ingest.fetch_gratefulstats.fetch_gratefulstats_citation",
        lambda online: [
            Citation(
                key="grateful_stats_api",
                title="Grateful Stats API (live probe)",
                url="https://www.gratefulstats.com/APIInfo.html",
                kind="api",
            ),
        ],
    )
    dump = load_gdshowsdb_vendor(FIXTURE_VENDOR)
    comp, report = merge_archival(
        MergeInputs(
            gdshows_dump=dump,
            curated_seed_dir=SEED_DIR,
            online=True,
            ia_max_rows=0,
            skip_truckin=True,
            skip_cmu=True,
            skip_whitegum=True,
            skip_wikipedia=True,
            skip_maximinus=True,
            skip_dead_net=True,
            skip_dead_net_songs=True,
        ),
    )
    assert "gratefulstats_api_probe" in report.sources_used
    assert len(comp.citations) >= 1
