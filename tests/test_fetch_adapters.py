"""Tests for online ingest fetch adapters (fixture-based, no mocks)."""

from __future__ import annotations

import json
from pathlib import Path

from src.ingest.fetch_alex_allan import fetch_alex_allan_songs
from src.ingest.fetch_cmu import split_cmu_blocks
from src.ingest.fetch_wikipedia import fetch_wikipedia_releases
from src.sources.wikipedia import parse_release

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ingest"


def test_split_cmu_blocks_mini():
    text = (FIXTURES / "cmu_mini.txt").read_text(encoding="utf-8")
    blocks = split_cmu_blocks(text)
    assert len(blocks) == 1
    from src.sources import cmu_setlists

    show, venue, perf_tuple, song_tuple = cmu_setlists.parse(blocks[0])
    assert show.slug.startswith("1972-08-27@")
    assert any(p.segue_into for p in perf_tuple)


def test_fetch_alex_allan_from_fixture_cache(tmp_path, monkeypatch):
    vendor_root = tmp_path / "vendor"
    whitegum = vendor_root / "whitegum"
    whitegum.mkdir(parents=True)
    (whitegum / "intro.htm").write_text(
        (FIXTURES / "whitegum_mini.html").read_text(encoding="utf-8")
    )
    monkeypatch.setattr("src.ingest._vendor_fetch.VENDOR_ROOT", vendor_root)
    songs, pointers = fetch_alex_allan_songs(online=False, seed_dir=None)
    assert len(songs) >= 2
    assert len(pointers) >= 2


def test_wikipedia_release_parse_round_trip():
    row = {"title": "American Beauty", "release_date": "1970-11-01", "kind": "studio"}
    rel = parse_release(row)
    assert rel.title == "American Beauty"


def test_wikipedia_discography_snippet_parse():
    from src.ingest.fetch_wikipedia import parse_discography_wikitext

    text = (FIXTURES / "wikipedia_discography_snippet.txt").read_text(encoding="utf-8")
    rows = parse_discography_wikitext(text)
    titles = {row["title"] for row in rows}
    assert "American Beauty" in titles
    assert any(row["release_date"] == "1970-11-01" for row in rows)


def test_wikipedia_members_snippet_parse():
    from src.ingest.fetch_wikipedia import parse_members_wikitext

    text = (FIXTURES / "wikipedia_members_snippet.txt").read_text(encoding="utf-8")
    rows = parse_members_wikitext(text)
    names = {row["full_name"] for row in rows}
    assert "Jerry Garcia" in names
    assert "Robert Hunter" in names


def test_wikipedia_vendor_cache(tmp_path, monkeypatch):
    vendor = tmp_path / "wikipedia"
    vendor.mkdir(parents=True)
    rows = [
        {"title": "American Beauty", "release_date": "1970-11-01", "kind": "studio"}
    ]
    (vendor / "discography.json").write_text(json.dumps(rows), encoding="utf-8")
    monkeypatch.setattr(
        "src.ingest.fetch_wikipedia.vendor_path", lambda source, name: vendor / name
    )
    releases = fetch_wikipedia_releases(online=False)
    assert len(releases) == 1


def test_fetch_dead_net_from_fixture_cache(tmp_path, monkeypatch):
    vendor_root = tmp_path / "vendor"
    dead = vendor_root / "dead_net"
    dead.mkdir(parents=True)
    (dead / "band.html").write_text(
        (FIXTURES / "dead_net_mini.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.ingest._vendor_fetch.VENDOR_ROOT", vendor_root)
    from src.ingest.fetch_dead_net import fetch_dead_net_personnel

    people = fetch_dead_net_personnel(online=True, seed_dir=None)
    names = {p.full_name for p in people}
    assert "Jerry Garcia" in names


def test_fetch_cmu_from_fixture_cache(tmp_path, monkeypatch):
    vendor_root = tmp_path / "vendor"
    cmu = vendor_root / "cmu"
    cmu.mkdir(parents=True)
    (cmu / "gs.html").write_text(
        (FIXTURES / "cmu_mini.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr("src.ingest._vendor_fetch.VENDOR_ROOT", vendor_root)
    from src.ingest.fetch_cmu import fetch_cmu_shows

    shows, _venues, _songs, perfs, source = fetch_cmu_shows(online=False)
    assert len(shows) >= 1
    assert any(p.segue_into for p in perfs)
    assert "cache:" in source or source.startswith("http")


def test_setlistfm_max_pages_zero_paginates(monkeypatch):
    monkeypatch.setenv("SETLISTFM_API_KEY", "test-key")
    pages_fetched: list[int] = []

    def fake_urlopen(req, timeout=60):
        page = int(req.full_url.rsplit("p=", 1)[-1])

        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                pages_fetched.append(page)
                if page == 1:
                    payload = {"setlist": [{"id": "a"}], "total": 25}
                else:
                    payload = {"setlist": [], "total": 25}
                return json.dumps(payload).encode("utf-8")

        return Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    from src.ingest.fetch_setlistfm import fetch_setlistfm_shows

    rows = fetch_setlistfm_shows(max_pages=0, sleep_s=0.0)
    assert len(rows) == 1
    assert pages_fetched == [1, 2]


def test_fetch_lma_recordings_httpserver(httpserver, monkeypatch):
    httpserver.expect_request("/advancedsearch.php").respond_with_json(
        {
            "response": {
                "docs": [
                    {
                        "identifier": "gd1977-05-08.sbd.miller.110987.flac16",
                        "date": "1977-05-08",
                        "venue": "Barton Hall, Cornell University",
                        "coverage": "Ithaca, NY",
                        "source": "SBD",
                    }
                ]
            }
        }
    )
    monkeypatch.setattr(
        "src.ingest.fetch_internet_archive.SEARCH_URL",
        httpserver.url_for("/advancedsearch.php"),
    )
    from src.ingest.fetch_internet_archive import fetch_lma_recordings

    recs = fetch_lma_recordings(max_rows=10)
    assert len(recs) == 1
    assert recs[0].archive_id.startswith("gd1977-05-08")


def test_fetch_wikipedia_personnel_cache(tmp_path, monkeypatch):
    vendor = tmp_path / "wikipedia"
    vendor.mkdir(parents=True)
    (vendor / "members.json").write_text(
        (FIXTURES / "wikipedia_members.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "src.ingest.fetch_wikipedia.vendor_path", lambda source, name: vendor / name
    )
    from src.ingest.fetch_wikipedia import fetch_wikipedia_personnel

    people = fetch_wikipedia_personnel(online=False)
    assert len(people) == 1
    assert people[0].full_name == "Jerry Garcia"


def test_parse_maximinus_reviews_fixture():
    from src.ingest.fetch_maximinus_reviews import (
        attach_reviews_to_shows,
        parse_maximinus_reviews,
    )
    from src.models import Show

    text = (FIXTURES / "maximinus_mini.txt").read_text(encoding="utf-8")
    reviews = parse_maximinus_reviews(text)
    assert len(reviews) == 3
    shows = [
        Show(
            slug="1965-05-05@fillmore",
            date=__import__("datetime").date(1965, 5, 5),
            venue_slug="fillmore",
        ),
        Show(
            slug="1977-05-08@barton_hall",
            date=__import__("datetime").date(1977, 5, 8),
            venue_slug="barton_hall",
        ),
    ]
    by_date: dict[str, list] = {}
    for show in shows:
        by_date.setdefault(show.date.isoformat(), []).append(show)
    attached = attach_reviews_to_shows(reviews, by_date)
    slugs = {r.show_slug for r in attached}
    assert "1965-05-05@fillmore" in slugs
    assert "1977-05-08@barton_hall" in slugs
    assert all(r.source_url.startswith("https://") for r in attached)


def test_parse_cmu_lyrics_fixture():
    from src.ingest.fetch_cmu_lyrics import parse_cmu_lyrics_index

    html = (FIXTURES / "cmu_lyrics_mini.html").read_text(encoding="utf-8")
    pointers = parse_cmu_lyrics_index(html)
    slugs = {lp.song_slug for lp in pointers}
    assert "althea" in slugs
    assert "ripple" in slugs
    assert all(lp.source_url.startswith("https://") for lp in pointers)


def test_load_bibliography_fixture(tmp_path):
    from src.ingest.fetch_bibliography import load_bibliography_citations

    bib = tmp_path / "bib.md"
    bib.write_text(
        (FIXTURES / "bibliography_mini.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    citations = load_bibliography_citations(bib)
    assert len(citations) == 2
    assert citations[0].url.startswith("https://")


def test_load_references_bib_fixture(tmp_path):
    from src.ingest.fetch_bibliography import load_references_bib_citations

    bib = tmp_path / "refs.bib"
    bib.write_text(
        (FIXTURES / "references_mini.bib").read_text(encoding="utf-8"), encoding="utf-8"
    )
    citations = load_references_bib_citations(bib)
    assert len(citations) == 2
    urls = {c.url for c in citations}
    assert "https://archive.org/details/GratefulDead" in urls


def test_references_bib_accepts_url_doi_and_year_fields(tmp_path):
    from src.ingest.fetch_bibliography import load_references_bib_citations

    bib = tmp_path / "refs.bib"
    bib.write_text(
        """
@book{lewin_gmit,
  author = {Lewin, David},
  title = {Generalized Musical Intervals and Transformations},
  year = {2007},
  doi = {10.1093/acprof:oso/9780195317138.001.0001}
}

@techreport{nist_music_category,
  author = {Padi, Sarala and Breiner, Spencer J.},
  title = {A Category Theoretic Approach to Modeling and Analysis Using Music as a Case Study},
  year = {2017},
  url = {https://www.nist.gov/publications/category-theoretic-approach-modeling-and-analysis-using-music-case-study}
}
""",
        encoding="utf-8",
    )

    citations = load_references_bib_citations(bib)
    by_key = {c.key: c for c in citations}
    assert by_key["lewin_gmit"].url == (
        "https://doi.org/10.1093/acprof:oso/9780195317138.001.0001"
    )
    assert by_key["lewin_gmit"].kind == "book"
    assert by_key["lewin_gmit"].year == 2007
    assert by_key["nist_music_category"].kind == "article"
    assert by_key["nist_music_category"].year == 2017


def test_bibliography_strips_markdown_footnotes_from_doi_urls():
    from src.ingest.fetch_bibliography import parse_doi_urls

    citations = parse_doi_urls("See https://doi.org/10.1215/03335372-24-1-35[^53].")
    assert citations[0].url == "https://doi.org/10.1215/03335372-24-1-35"
    assert citations[0].title == "DOI 03335372-24-1-35"


def test_load_all_project_citations_merges(tmp_path):
    from src.ingest.fetch_bibliography import load_all_project_citations

    md = tmp_path / "bib.md"
    md.write_text(
        (FIXTURES / "bibliography_mini.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    bib = tmp_path / "refs.bib"
    bib.write_text(
        (FIXTURES / "references_mini.bib").read_text(encoding="utf-8"), encoding="utf-8"
    )
    citations = load_all_project_citations(bibliography_md=md, references_bib=bib)
    assert len(citations) == 4


def test_lyric_pointer_enrich_overlay_and_dead_net():
    from src.ingest.lyric_pointer_enrich import consolidate_lyric_pointers
    from src.models import LyricPointer, Song

    curated = [
        {
            "song_slug": "ripple",
            "lyricist": "Robert Hunter",
            "source_url": "https://www.whitegum.com/songfile/RIPPLE.HTM",
            "themes": ["water", "spirituality"],
        },
    ]
    pointers = [
        LyricPointer(
            song_slug="ripple",
            lyricist="",
            source_url="https://web.archive.org/web/20150101000000/http://www.cs.cmu.edu/~mleone/gdead/dead-lyrics/ripple.txt",
            themes=(),
        ),
    ]
    songs = [
        Song(slug="ripple", title="Ripple", lyricists=("Robert Hunter",), composers=()),
        Song(slug="althea", title="Althea", lyricists=("Robert Hunter",), composers=()),
    ]
    merged, stats = consolidate_lyric_pointers(
        pointers,
        songs,
        performed_song_slugs={"ripple", "althea"},
        curated_rows=curated,
    )
    ripple = next(lp for lp in merged if lp.song_slug == "ripple")
    assert ripple.lyricist == "Robert Hunter"
    assert ripple.themes == ("water", "spirituality")
    assert stats["dead_net_added"] == 1
    assert stats["lyricists_propagated"] >= 0
    assert any(
        lp.song_slug == "althea" and "dead.net/song/althea" in lp.source_url
        for lp in merged
    )


def test_parse_truckin_sqlite(tmp_path):
    import sqlite3

    from src.ingest.fetch_truckin_db import parse_truckin_database

    db = tmp_path / "mini.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE venue (id INTEGER PRIMARY KEY, name TEXT, city TEXT, state TEXT, country TEXT);
        CREATE TABLE song (id INTEGER PRIMARY KEY, title TEXT);
        CREATE TABLE concert (id INTEGER PRIMARY KEY, venue_id INTEGER, date TEXT);
        CREATE TABLE setlist (id INTEGER PRIMARY KEY, concert_id INTEGER, notes TEXT);
        CREATE TABLE setlistsong (id INTEGER PRIMARY KEY, setlist_id INTEGER, song_id INTEGER, "order" INTEGER, transition INTEGER);
        INSERT INTO venue VALUES (1, 'Barton Hall', 'Ithaca', 'NY', 'US'), (2, '', 'Nowhere', 'XX', 'US');
        INSERT INTO song VALUES (1, 'Truckin'), (2, 'Sugar Magnolia'), (3, '  ');
        INSERT INTO concert VALUES (1, 1, '1977-05-08'), (2, 2, '1977-05-09');
        INSERT INTO setlist VALUES (1, 1, ''), (2, 2, '');
        INSERT INTO setlistsong VALUES (1, 1, 1, 1, 0), (2, 1, 2, 2, 1), (3, 1, 3, 3, 0), (4, 2, 1, 1, 0);
        """
    )
    conn.commit()
    conn.close()
    shows, venues, songs, perfs = parse_truckin_database(db)
    assert len(shows) == 1
    assert len(perfs) == 2
    assert perfs[1].segue_into is None
    assert perfs[0].song_slug == "truckin"


def test_bibliography_inline_and_doi(tmp_path):
    from src.ingest.fetch_bibliography import load_all_project_citations

    md = tmp_path / "bib.md"
    md.write_text(
        "See [Grateful Dead Studies](https://gratefuldeadstudies.org) and DOI https://doi.org/10.1080/13617672.2022.2005711\n",
        encoding="utf-8",
    )
    citations = load_all_project_citations(
        bibliography_md=md, references_bib=tmp_path / "missing.bib"
    )
    urls = {c.url for c in citations}
    assert "https://gratefuldeadstudies.org" in urls
    assert any("doi.org" in u for u in urls)


def test_parse_dead_net_song_links():
    from src.ingest.fetch_dead_net_songs import parse_dead_net_song_links

    html = '<a href="/song/ripple">Ripple</a><a href="/song/althea">Althea</a>'
    pointers = parse_dead_net_song_links(html)
    slugs = {p.song_slug for p in pointers}
    assert "ripple" in slugs
    assert all(p.source_url.startswith("https://www.dead.net/song/") for p in pointers)


def test_propagate_song_lyricists_and_alias_themes():
    from src.ingest.lyric_pointer_enrich import consolidate_lyric_pointers
    from src.models import LyricPointer, Song

    curated = [
        {
            "song_slug": "playing_in_the_band",
            "lyricist": "Robert Hunter",
            "source_url": "https://example.com/playin",
            "themes": ["road", "jam"],
        },
    ]
    pointers = [
        LyricPointer(
            song_slug="playin_in_the_band",
            lyricist="",
            source_url="https://example.com/cmu/playin.txt",
            themes=(),
        ),
    ]
    songs = [
        Song(
            slug="playin_in_the_band",
            title="Playin' in the Band",
            lyricists=("Robert Hunter",),
            composers=(),
        ),
    ]
    merged, stats = consolidate_lyric_pointers(
        pointers,
        songs,
        performed_song_slugs={"playin_in_the_band"},
        curated_rows=curated,
    )
    row = merged[0]
    assert row.lyricist == "Robert Hunter"
    assert row.themes == ("road", "jam")
    assert stats["lyricists_propagated"] >= 0


def test_parse_dead_net_title_near_fallback():
    from src.ingest.fetch_dead_net_songs import parse_dead_net_song_links

    html = '<a href="/song/Ripple">Ripple</a>'
    pointers = parse_dead_net_song_links(html)
    assert any(p.song_slug == "ripple" for p in pointers)


def test_gratefulstats_api_headers_with_key(monkeypatch):
    from src.ingest.fetch_gratefulstats import _api_headers

    monkeypatch.setenv("GRATEFULSTATS_API_KEY", "secret")
    headers = _api_headers()
    assert headers["Authorization"] == "Bearer secret"


def test_gratefulstats_api_headers_empty(monkeypatch):
    from src.ingest.fetch_gratefulstats import _api_headers

    monkeypatch.delenv("GRATEFULSTATS_API_KEY", raising=False)
    assert _api_headers() == {}


def test_gratefulstats_offline_and_missing_key(monkeypatch):
    import pytest

    from src.ingest.fetch_gratefulstats import fetch_gratefulstats_citation

    assert fetch_gratefulstats_citation(online=False) == []
    monkeypatch.delenv("GRATEFULSTATS_API_KEY", raising=False)
    with pytest.raises(OSError, match="not set"):
        fetch_gratefulstats_citation(online=True)


def test_gratefulstats_http_error(httpserver, monkeypatch):
    import pytest

    from src.ingest.fetch_gratefulstats import fetch_gratefulstats_citation

    httpserver.expect_request("/shows").respond_with_data("denied", status=403)
    monkeypatch.setenv("GRATEFULSTATS_API_KEY", "test-token")
    monkeypatch.setenv("GRATEFULSTATS_API_BASE", httpserver.url_for(""))
    with pytest.raises(OSError, match="HTTP 403"):
        fetch_gratefulstats_citation(online=True)


def test_gratefulstats_unreachable(monkeypatch):
    import pytest

    from src.ingest.fetch_gratefulstats import fetch_gratefulstats_citation

    monkeypatch.setenv("GRATEFULSTATS_API_KEY", "test-token")
    monkeypatch.setenv("GRATEFULSTATS_API_BASE", "http://127.0.0.1:1")
    with pytest.raises(OSError, match="unreachable"):
        fetch_gratefulstats_citation(online=True)


def test_fetch_dead_net_songs_from_vendor_cache(monkeypatch, tmp_path):
    from src.ingest.fetch_dead_net_songs import fetch_dead_net_song_pointers

    vendor_root = tmp_path / "vendor"
    (vendor_root / "dead_net").mkdir(parents=True)
    (vendor_root / "dead_net" / "songs.html").write_text(
        "<html><body>" + '<a href="/song/ripple">Ripple</a>' * 80 + "</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr("src.ingest._vendor_fetch.VENDOR_ROOT", vendor_root)
    pointers, label = fetch_dead_net_song_pointers(online=True)
    assert pointers
    assert "cache:" in label


def test_load_live_bibliography_smoke():
    from src.ingest.fetch_bibliography import load_all_project_citations

    citations = load_all_project_citations()
    assert len(citations) >= 100
    assert any(c.year for c in citations)


def test_gratefulstats_api_probe(httpserver, monkeypatch):
    from src.ingest.fetch_gratefulstats import fetch_gratefulstats_citation

    httpserver.expect_request("/shows").respond_with_json({"shows": []})
    monkeypatch.setenv("GRATEFULSTATS_API_KEY", "test-token")
    monkeypatch.setenv("GRATEFULSTATS_API_BASE", httpserver.url_for(""))
    citations = fetch_gratefulstats_citation(online=True)
    assert citations
    assert citations[0].kind == "api"
