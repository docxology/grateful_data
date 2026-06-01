"""Tests for source-specific parsers — real-content fixtures, no mocks."""

from __future__ import annotations

import pytest

from src.sources import (
    alex_allan,
    cmu_setlists,
    dead_net,
    gdsets,
    gdshowsdb,
    internet_archive,
    setlist_program,
    setlistfm,
    wikipedia,
)


def test_setlistfm_parses_dd_mm_yyyy_date():
    payload = {
        "eventDate": "08-05-1977",
        "venue": {
            "name": "Barton Hall",
            "city": {
                "name": "Ithaca",
                "stateCode": "NY",
                "country": {"code": "USA"},
            },
        },
        "sets": {
            "set": [
                {
                    "song": [
                        {"name": "Scarlet Begonias"},
                        {"name": "Fire on the Mountain"},
                    ]
                }
            ]
        },
    }
    show, venue, perfs, songs = setlistfm.parse(payload)
    assert show.date.isoformat() == "1977-05-08"
    assert venue.city == "Ithaca"
    assert {s.title for s in songs} == {"Scarlet Begonias", "Fire on the Mountain"}
    assert len(perfs) == 2
    assert setlistfm.CITATION_KEY == "setlistfm_gd"


def test_setlistfm_parses_iso_date_too():
    payload = {
        "eventDate": "1977-05-08",
        "venue": {"name": "Barton Hall", "city": {"name": "Ithaca", "stateCode": "NY"}},
        "sets": {"set": []},
    }
    show, _venue, _perfs, _songs = setlistfm.parse(payload)
    assert show.date.year == 1977


def test_setlistfm_rejects_bad_date():
    with pytest.raises(ValueError):
        setlistfm.parse(
            {
                "eventDate": "lol",
                "venue": {"name": "X", "city": {"name": "Y"}},
                "sets": {"set": []},
            }
        )


def test_cmu_setlists_basic_and_segues():
    text = """1972-08-27 Old Renaissance Faire Grounds, Veneta, OR
Set 1: Promised Land, Sugaree, Mr. Charlie
Set 2: China Cat Sunflower-> I Know You Rider, Truckin'
Encore: One More Saturday Night"""
    show, venue, perfs, songs = cmu_setlists.parse(text)
    assert show.date.isoformat() == "1972-08-27"
    assert venue.city == "Veneta"
    titles = [s.title for s in songs]
    assert "China Cat Sunflower" in titles
    cc = [p for p in perfs if p.song_slug == "china_cat_sunflower"][0]
    assert cc.segue_into == "i_know_you_rider"
    assert cmu_setlists.CITATION_KEY


def test_cmu_setlists_encore_segue_and_first_song_segue():
    text = """1977-05-08 Barton Hall, Ithaca, NY
Set 1: Scarlet Begonias-> Fire on the Mountain
Encore: One More Saturday Night-> Casey Jones"""
    show, _venue, perfs, _songs = cmu_setlists.parse(text)
    assert show.date.isoformat() == "1977-05-08"
    scarlet = [p for p in perfs if p.song_slug == "scarlet_begonias"][0]
    assert scarlet.segue_into == "fire_on_the_mountain"
    encore = [p for p in perfs if p.song_slug == "one_more_saturday_night"][0]
    assert encore.segue_into == "casey_jones"


def test_cmu_setlists_trailing_arrow_without_successor():
    text = """1972-08-27 Old Renaissance Faire Grounds, Veneta, OR
Set 1: China Cat Sunflower->"""
    _show, _venue, perfs, _songs = cmu_setlists.parse(text)
    cc = [p for p in perfs if p.song_slug == "china_cat_sunflower"][0]
    assert cc.segue_into is None


def test_cmu_setlists_parse_many_and_rejects_empty():
    text = """1972-08-27 Old Renaissance Faire Grounds, Veneta, OR
Set 1: Sugaree"""
    out = cmu_setlists.parse_many([text, text])
    assert len(out) == 2
    with pytest.raises(ValueError):
        cmu_setlists.parse("")
    with pytest.raises(ValueError):
        cmu_setlists.parse("no-header-here\nSet 1: Sugaree")


def test_setlist_program_record():
    text = """DATE: 1977-05-08
VENUE: Barton Hall
CITY: Ithaca
STATE: NY
SET 1: Minglewood Blues; Loser
SET 2: Scarlet Begonias > Fire on the Mountain; Estimated Prophet
ENCORE: One More Saturday Night"""
    show, venue, perfs, songs = setlist_program.parse(text)
    assert show.date.isoformat() == "1977-05-08"
    assert venue.name == "Barton Hall"
    sb = [p for p in perfs if p.song_slug == "scarlet_begonias"][0]
    assert sb.segue_into == "fire_on_the_mountain"
    assert {s.title for s in songs} >= {"Loser", "Estimated Prophet"}


def test_setlist_program_parse_many_and_rejects_missing_fields():
    text = """DATE: 1977-05-08
VENUE: Barton Hall
CITY: Ithaca
STATE: NY
SET 1: Loser"""
    out = setlist_program.parse_many([text])
    assert len(out) == 1
    with pytest.raises(ValueError):
        setlist_program.parse("SET 1: Loser")


def test_gdsets_returns_memorabilia():
    record = {
        "date": "1989-07-07",
        "venue": "JFK Stadium",
        "city": "Philadelphia",
        "state": "PA",
        "setlist": [{"set": 1, "songs": ["Touch of Grey", "Hell in a Bucket"]}],
        "memorabilia": [{"kind": "ticket", "url": "https://gdsets.com/x"}],
    }
    show, venue, perfs, songs, mem = gdsets.parse(record)
    assert show.date.year == 1989
    assert mem == (("ticket", "https://gdsets.com/x"),)
    assert {s.title for s in songs} == {"Touch of Grey", "Hell in a Bucket"}


def test_gdshowsdb_dump_round_trip():
    dump = {
        "venues": [
            {
                "venue_slug": "fillmore_west_san_francisco",
                "name": "Fillmore West",
                "city": "San Francisco",
                "state": "CA",
            }
        ],
        "songs": [
            {
                "song_slug": "dark_star",
                "title": "Dark Star",
                "composers": ["Garcia"],
                "lyricists": ["Hunter"],
            }
        ],
        "shows": [
            {
                "show_slug": "ignored",
                "date": "1969-02-27",
                "venue_slug": "fillmore_west_san_francisco",
                "tour": "1969 Winter",
            }
        ],
        "performances": [
            {
                "show_slug": "1969-02-27@fillmore_west_san_francisco",
                "song_slug": "dark_star",
                "set_number": 1,
                "position": 1,
            }
        ],
    }
    shows, venues, songs, perfs = gdshowsdb.parse(dump)
    assert shows[0].slug == "1969-02-27@fillmore_west_san_francisco"
    assert venues[0].city == "San Francisco"
    assert songs[0].composers == ("Garcia",)
    assert perfs[0].song_slug == "dark_star"


def test_internet_archive_recording_parse():
    payload = {
        "metadata": {
            "identifier": "gd1977-05-08.sbd.miller.110987.flac16",
            "date": "1977-05-08",
            "venue": "Barton Hall, Cornell University",
            "coverage": "Ithaca, NY",
            "source": "MATRIX",
        }
    }
    rec = internet_archive.parse(payload)
    assert rec.source_type == "MTX"
    assert rec.archive_id.startswith("gd1977-05-08")
    assert rec.url.startswith("https://archive.org/")


def test_internet_archive_preserves_explicit_show_slug():
    payload = {
        "metadata": {
            "identifier": "gd1977-05-08.sbd.miller.110987.flac16",
            "date": "1977-05-08",
            "venue": "Barton Hall",
            "coverage": "Ithaca, NY",
            "source": "SBD",
            "show_slug": "1977-05-08@barton_hall_cornell_university_ithaca",
        }
    }
    rec = internet_archive.parse(payload)
    assert rec.show_slug == "1977-05-08@barton_hall_cornell_university_ithaca"


def test_date_from_archive_id_two_digit_year():
    assert (
        internet_archive.date_from_archive_id("gd67-01-27.aud.hanno.16744.sbeok.shnf")
        == "1967-01-27"
    )
    assert (
        internet_archive.date_from_archive_id("gd1977-05-08.sbd.miller.110987.flac16")
        == "1977-05-08"
    )
    assert (
        internet_archive.date_from_archive_id("gd1985-03-38.163427.sbeok.shnf") is None
    )


def test_internet_archive_iso_datetime_date():
    payload = {
        "metadata": {
            "identifier": "gd1984-05-08.test",
            "date": "1984-05-08T00:00:00Z",
            "venue": "Greek Theatre",
            "coverage": "Berkeley, CA",
            "source": "SBD",
        }
    }
    rec = internet_archive.parse(payload)
    assert rec.show_slug.startswith("1984-05-08@")


def test_internet_archive_unknown_source_label_defaults():
    payload = {
        "metadata": {
            "identifier": "x",
            "date": "1977-05-08",
            "venue": "Barton Hall",
            "coverage": "Ithaca, NY",
            "source": "WEIRD",
        }
    }
    rec = internet_archive.parse(payload)
    assert rec.source_type == "UNKNOWN"


def test_alex_allan_song_full_record():
    record = {
        "title": "Box of Rain",
        "composers": ["Phil Lesh"],
        "lyricists": ["Robert Hunter"],
        "first_performed": "1972-03-23",
        "last_performed": "1995-07-09",
        "aliases": ["Box (Phil)"],
    }
    song = alex_allan.parse(record)
    assert song.composers == ("Phil Lesh",)
    assert song.first_performed.year == 1972
    assert song.aliases == ("Box (Phil)",)


def test_alex_allan_song_partial_record():
    record = {"title": "Drums"}
    song = alex_allan.parse(record)
    assert song.first_performed is None
    assert song.composers == ()


def test_dead_net_person_parse():
    record = {
        "slug": "hart",
        "full_name": "Mickey Hart",
        "intervals": [
            {"start": "1967-09-30", "end": "1971-02-18", "role": "percussion"},
            {"start": "1974-10-20", "role": "percussion"},
        ],
    }
    p = dead_net.parse(record)
    assert p.active_on(__import__("datetime").date(1980, 1, 1))


def test_wikipedia_release_and_person():
    release = wikipedia.parse_release(
        {
            "title": "American Beauty",
            "release_date": "1970-11-01",
            "kind": "studio",
        }
    )
    assert release.kind == "studio"
    person = wikipedia.parse_person(
        {
            "slug": "garcia",
            "full_name": "Jerry Garcia",
            "intervals": [
                {"start": "1965-12-04", "end": "1995-08-09", "role": "lead guitar"}
            ],
        }
    )
    assert person.full_name.startswith("Jerry")
