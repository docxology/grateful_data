"""End-to-end seed load test."""

from __future__ import annotations

from src.seed import load_seed_compendium


def test_load_seed_basic_shape(compendium):
    assert compendium is not None
    assert len(compendium.shows) >= 80
    assert len(compendium.venues) >= 20
    assert len(compendium.songs) >= 70
    assert len(compendium.people) == 14
    # Every show's venue_slug is in venues
    venue_slugs = {v.slug for v in compendium.venues}
    for s in compendium.shows:
        assert s.venue_slug in venue_slugs
    # Every performance points at a known show and song
    known_show_slugs = {s.slug for s in compendium.shows}
    known_song_slugs = {s.slug for s in compendium.songs}
    for p in compendium.performances:
        assert p.show_slug in known_show_slugs
        assert p.song_slug in known_song_slugs


def test_load_seed_explicit_dir(tmp_path):
    # Load via the public load_seed_compendium path; uses default dir.
    comp = load_seed_compendium()
    assert len(comp.citations) >= 25
    for c in comp.citations:
        assert c.url.startswith("http")


def test_seed_citations_cover_brief(compendium):
    keys = {c.key for c in compendium.citations}
    expected = {
        "cmu_leone_setlists",
        "setlists_net_program",
        "gdsets_com",
        "setlistfm_gd",
        "grateful_stats",
        "gdshowsdb",
        "jerry_pycia",
        "cmu_leone_lyrics",
        "whitegum_alex_allan",
        "dead_net_official",
        "wikipedia_gd",
        "britannica_gd",
        "wikipedia_discography",
        "fifteen_songs_dataset",
        "gd_reviews_corpus",
        "internet_archive_lma",
    }
    missing = expected - keys
    assert not missing, f"missing citation keys: {missing}"
