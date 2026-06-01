"""Tests for bundled seed JSON parsers."""

from __future__ import annotations

from datetime import date

from src.sources.seed_bundle import (
    parse_citation_record,
    parse_review_record,
    parse_show_records,
    parse_venue_record,
)


def test_parse_venue_record():
    v = parse_venue_record(
        {
            "slug": "barton_hall_ithaca",
            "name": "Barton Hall",
            "city": "Ithaca",
            "state": "NY",
        }
    )
    assert v.slug == "barton_hall_ithaca"
    assert v.city == "Ithaca"


def test_parse_show_records_builds_performances():
    shows, perfs = parse_show_records(
        [
            {
                "date": "1977-05-08",
                "venue_slug": "barton_hall_ithaca",
                "setlist": [[1, ["Scarlet Begonias", "Fire on the Mountain"]]],
            }
        ]
    )
    assert len(shows) == 1
    assert shows[0].date == date(1977, 5, 8)
    assert shows[0].slug == "1977-05-08@barton_hall_ithaca"
    assert len(perfs) == 2
    assert perfs[0].position == 1
    assert perfs[1].song_slug == "fire_on_the_mountain"


def test_parse_citation_and_review_records():
    c = parse_citation_record(
        {"key": "x", "title": "T", "url": "https://example.com", "kind": "web"}
    )
    assert c.key == "x"
    c2 = parse_citation_record(
        {
            "key": "doi_key",
            "title": "DOI 77.1.1[^54",
            "url": "https://doi.org/10.1093/sf/77.1.1[^54",
            "kind": "article",
        }
    )
    assert c2.title == "DOI 77.1.1"
    assert c2.url == "https://doi.org/10.1093/sf/77.1.1"
    r = parse_review_record(
        {
            "show_slug": "1977-05-08@barton_hall_ithaca",
            "author": "A",
            "sentiment": 0.5,
            "summary": "ok",
            "source_url": "https://example.com/r",
            "kind": "fan",
        }
    )
    assert r.kind == "fan"
