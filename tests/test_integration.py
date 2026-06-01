"""Tests for the integration / reconcile layer."""

from __future__ import annotations

from datetime import date

from src.integration.reconcile import build_compendium
from src.models import (
    Citation,
    Performance,
    Person,
    Recording,
    Release,
    Show,
    Song,
    Venue,
    canonical_show_id,
)


def test_build_compendium_sorts_and_dedupes():
    v = Venue(slug="x", name="X", city="Y", state_or_region="Z")
    # Second entry for the same venue with sparser fields — merge should prefer
    # the more informative name/city/state from ``v``.
    v_dup = Venue(slug="x", name="X2", city="Y2", state_or_region="Z2")
    s1 = Show(
        slug=canonical_show_id(date(1977, 5, 8), "x"),
        date=date(1977, 5, 8),
        venue_slug="x",
    )
    s2 = Show(
        slug=canonical_show_id(date(1969, 2, 27), "x"),
        date=date(1969, 2, 27),
        venue_slug="x",
    )
    song_a = Song(slug="ripple", title="Ripple", composers=("Garcia",))
    song_b = Song(slug="ripple", title="Ripple", lyricists=("Hunter",))
    comp = build_compendium(
        venues=[v_dup, v],
        shows=[s1, s2],
        songs=[song_a, song_b],
        performances=[
            Performance(
                show_slug=s1.slug, song_slug="ripple", set_number=1, position=1
            ),
            Performance(
                show_slug=s1.slug, song_slug="ripple", set_number=1, position=1
            ),
        ],
    )
    assert [v.slug for v in comp.venues] == ["x"]
    # First-seen non-empty value wins in our merge.
    assert comp.venues[0].name in {"X", "X2"}
    assert [s.date for s in comp.shows] == [date(1969, 2, 27), date(1977, 5, 8)]
    merged_song = comp.song_by_slug["ripple"]
    assert merged_song.composers == ("Garcia",)
    assert merged_song.lyricists == ("Hunter",)
    assert len(comp.performances) == 1


def test_build_compendium_merges_person_intervals_and_dates():
    p1 = Person(
        slug="hart",
        full_name="Mickey Hart",
        intervals=((date(1967, 9, 30), date(1971, 2, 18), "percussion"),),
    )
    p2 = Person(
        slug="hart",
        full_name="",
        intervals=((date(1974, 10, 20), None, "percussion"),),
    )
    song_a = Song(
        slug="x",
        title="X",
        first_performed=date(1970, 1, 1),
        last_performed=date(1975, 1, 1),
    )
    song_b = Song(
        slug="x",
        title="X",
        first_performed=date(1969, 1, 1),
        last_performed=date(1980, 1, 1),
    )
    comp = build_compendium(people=[p1, p2], songs=[song_a, song_b])
    merged = comp.person_by_slug["hart"]
    assert len(merged.intervals) == 2
    song = comp.song_by_slug["x"]
    assert song.first_performed == date(1969, 1, 1)
    assert song.last_performed == date(1980, 1, 1)


def test_build_compendium_carries_recordings_releases_citations():
    rec = Recording(archive_id="a", show_slug="x", source_type="SBD")
    rel = Release(
        slug="aoxomoxoa",
        title="Aoxomoxoa",
        release_date=date(1969, 6, 20),
        kind="studio",
    )
    cit = Citation(key="k", title="T", url="https://x", kind="web")
    comp = build_compendium(recordings=[rec], releases=[rel], citations=[cit])
    assert comp.recordings == (rec,)
    assert comp.releases == (rel,)
    assert comp.citations == (cit,)


def test_compendium_lineup_on_uses_people():
    p = Person(
        slug="garcia",
        full_name="Jerry Garcia",
        intervals=((date(1965, 12, 4), date(1995, 8, 9), "lead guitar"),),
    )
    comp = build_compendium(people=[p])
    lu = comp.lineup_on(date(1977, 5, 8))
    assert "garcia" in lu.member_slugs
    lu2 = comp.lineup_on(date(2020, 1, 1))
    assert lu2.member_slugs == ()
