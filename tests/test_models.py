"""Tests for the schema in ``src/models.py``."""

from __future__ import annotations

from datetime import date

import pytest

from src.models import (
    Citation,
    Lineup,
    Performance,
    Person,
    Recording,
    Release,
    Show,
    Song,
    Venue,
    canonical_show_id,
    canonical_song_id,
    lineup_on,
)


def test_canonical_song_id_strips_punctuation_and_unicode():
    assert canonical_song_id("Sugar Magnolia") == "sugar_magnolia"
    assert canonical_song_id("Mr. Charlie") == "mr_charlie"
    assert canonical_song_id("Mississippi Half-Step Uptown Toodeloo").startswith(
        "mississippi_half_step"
    )


def test_canonical_song_id_rejects_empty():
    with pytest.raises(ValueError):
        canonical_song_id("")


def test_canonical_show_id_format():
    assert canonical_show_id(date(1977, 5, 8), "barton_hall_ithaca") == (
        "1977-05-08@barton_hall_ithaca"
    )


def test_canonical_show_id_rejects_empty_venue():
    with pytest.raises(ValueError):
        canonical_show_id(date(1977, 5, 8), "")


def test_venue_validates_required_fields():
    Venue(slug="x", name="X", city="Y", state_or_region="Z")
    with pytest.raises(ValueError):
        Venue(slug="", name="X", city="Y", state_or_region="Z")
    with pytest.raises(ValueError):
        Venue(slug="x", name="", city="Y", state_or_region="Z")


def test_person_validates_role_and_interval_ordering():
    Person(
        slug="garcia",
        full_name="Jerry Garcia",
        intervals=((date(1965, 1, 1), date(1995, 8, 9), "lead guitar"),),
    )
    with pytest.raises(ValueError):
        Person(slug="", full_name="J", intervals=())
    with pytest.raises(ValueError):
        Person(
            slug="x",
            full_name="X",
            intervals=((date(1995, 1, 1), date(1990, 1, 1), "drums"),),
        )
    with pytest.raises(ValueError):
        Person(
            slug="x",
            full_name="X",
            intervals=((date(1990, 1, 1), None, "frontman"),),
        )


def test_person_active_on():
    p = Person(
        slug="hart",
        full_name="Mickey Hart",
        intervals=(
            (date(1967, 9, 30), date(1971, 2, 18), "percussion"),
            (date(1974, 10, 20), None, "percussion"),
        ),
    )
    assert p.active_on(date(1968, 1, 1))
    assert not p.active_on(date(1972, 1, 1))
    assert p.active_on(date(2000, 1, 1))


def test_song_validates_dates():
    Song(
        slug="ripple",
        title="Ripple",
        first_performed=date(1970, 8, 18),
        last_performed=date(1995, 7, 9),
    )
    with pytest.raises(ValueError):
        Song(
            slug="x",
            title="X",
            first_performed=date(1995, 1, 1),
            last_performed=date(1970, 1, 1),
        )
    with pytest.raises(ValueError):
        Song(slug="", title="Foo")
    with pytest.raises(ValueError):
        Song(slug="foo", title="")


def test_show_slug_must_match_canonical():
    slug = canonical_show_id(date(1977, 5, 8), "barton_hall_ithaca")
    Show(slug=slug, date=date(1977, 5, 8), venue_slug="barton_hall_ithaca")
    with pytest.raises(ValueError):
        Show(slug="bad", date=date(1977, 5, 8), venue_slug="barton_hall_ithaca")
    with pytest.raises(ValueError):
        Show(slug=slug, date=date(1977, 5, 8), venue_slug="")


def test_performance_validates_positions():
    Performance(show_slug="s", song_slug="x", set_number=1, position=1)
    with pytest.raises(ValueError):
        Performance(show_slug="s", song_slug="x", set_number=0, position=1)
    with pytest.raises(ValueError):
        Performance(show_slug="s", song_slug="x", set_number=1, position=0)


def test_recording_validates_source_type():
    Recording(archive_id="gd1977-05-08", show_slug="x", source_type="SBD")
    with pytest.raises(ValueError):
        Recording(archive_id="x", show_slug="x", source_type="NOPE")
    with pytest.raises(ValueError):
        Recording(archive_id="", show_slug="x", source_type="SBD")


def test_release_validates_kind():
    Release(slug="x", title="X", release_date=date(1973, 11, 15), kind="studio")
    with pytest.raises(ValueError):
        Release(slug="x", title="X", release_date=date(1973, 11, 15), kind="EP")


def test_citation_validates_kind():
    Citation(key="k", title="T", url="https://x", kind="web")
    with pytest.raises(ValueError):
        Citation(key="k", title="T", url="https://x", kind="zine")
    with pytest.raises(ValueError):
        Citation(key="", title="T", url="https://x", kind="web")
    with pytest.raises(ValueError):
        Citation(key="k", title="T", url="", kind="web")


def test_lineup_fingerprint_is_deterministic():
    a = Lineup(on_date=date(1977, 5, 8), member_slugs=("garcia", "weir", "lesh"))
    b = Lineup(on_date=date(1977, 5, 8), member_slugs=("lesh", "garcia", "weir"))
    assert a.fingerprint == b.fingerprint
    # Empty lineups are allowed (the empty set is a valid object in Set).
    Lineup(on_date=date(1977, 5, 8), member_slugs=())
    with pytest.raises(ValueError):
        Lineup(on_date=date(1977, 5, 8), member_slugs=("a", "a"))


def test_lineup_on_pure_function():
    p1 = Person(
        slug="a",
        full_name="A",
        intervals=((date(1970, 1, 1), date(1975, 1, 1), "lead guitar"),),
    )
    p2 = Person(
        slug="b",
        full_name="B",
        intervals=((date(1972, 1, 1), None, "drums"),),
    )
    lu = lineup_on([p1, p2], date(1973, 6, 1))
    assert set(lu.member_slugs) == {"a", "b"}
    lu2 = lineup_on([p1, p2], date(1980, 1, 1))
    assert lu2.member_slugs == ("b",)
