"""Tests for the schema additions (LyricPointer, Review) and the new analyses."""

from __future__ import annotations

import pytest

from src.analysis import (
    composers,
    eras,
    lyrics,
    personnel_timeline,
    reviews,
    segues,
)
from src.integration import canonicalize_alias
from src.integration.reconcile import build_compendium
from src.models import LyricPointer, Review


def test_lyric_pointer_validates_url():
    LyricPointer(song_slug="x", lyricist="L", source_url="https://x", themes=("a",))
    with pytest.raises(ValueError):
        LyricPointer(song_slug="", lyricist="L", source_url="https://x")
    with pytest.raises(ValueError):
        LyricPointer(song_slug="x", lyricist="L", source_url="ftp://nope")


def test_review_validates_fields():
    Review(
        show_slug="s",
        author="a",
        sentiment=0.5,
        summary="s",
        source_url="https://x",
        kind="fan",
    )
    with pytest.raises(ValueError):
        Review(
            show_slug="s",
            author="a",
            sentiment=1.5,
            summary="s",
            source_url="https://x",
            kind="fan",
        )
    with pytest.raises(ValueError):
        Review(
            show_slug="s",
            author="a",
            sentiment=0.5,
            summary="s",
            source_url="https://x",
            kind="critic",
        )
    with pytest.raises(ValueError):
        Review(
            show_slug="",
            author="a",
            sentiment=0.5,
            summary="s",
            source_url="https://x",
            kind="fan",
        )


def test_canonicalize_alias_known_and_unknown():
    assert canonicalize_alias("playin_in_the_band") == "playing_in_the_band"
    assert canonicalize_alias("bertha_reprise") == "bertha"
    assert canonicalize_alias("nonsense_xyz") == "nonsense_xyz"


def test_build_compendium_carries_lyrics_and_reviews():
    lp = LyricPointer(song_slug="ripple", lyricist="Hunter", source_url="https://x")
    rv = Review(
        show_slug="s",
        author="a",
        sentiment=0.9,
        summary="great",
        source_url="https://y",
        kind="fan",
    )
    comp = build_compendium(lyric_pointers=[lp], reviews=[rv])
    assert comp.lyric_pointers == (lp,)
    assert comp.reviews == (rv,)


def test_composers_three_views(compendium):
    cs = composers.composer_song_counts(compendium)
    ls = composers.lyricist_song_counts(compendium)
    cps = composers.composer_performance_counts(compendium)
    assert "Jerry Garcia" in cs
    assert "Robert Hunter" in ls
    assert cps["Jerry Garcia"] >= cs["Jerry Garcia"]  # weighted >= unweighted


def test_segue_edges_and_degrees(compendium):
    edges = segues.segue_edges(compendium)
    out_deg = segues.segue_out_degree(compendium)
    in_deg = segues.segue_in_degree(compendium)
    # Edge counts and out-degree sums match.
    assert sum(e.count for e in edges) == sum(out_deg.values()) == sum(in_deg.values())
    # If there are segues in the seed they should be sorted by count desc.
    counts = [e.count for e in edges]
    assert counts == sorted(counts, reverse=True)


def test_eras_partition_is_total(compendium):
    by_era = eras.shows_by_era(compendium)
    perf_by_era = eras.performances_by_era(compendium)
    assert sum(by_era.values()) == len(compendium.shows)
    assert sum(perf_by_era.values()) == len(compendium.performances)
    density = eras.year_month_density(compendium)
    assert sum(density.values()) == len(compendium.shows)
    # Unknown only happens for dates outside the active years.
    from datetime import date

    assert eras.era_of(date(1900, 1, 1)) == "Unknown"


def test_lyrics_theme_views(compendium):
    freq = lyrics.theme_frequencies(compendium)
    assert sum(freq.values()) >= 1
    by_era = lyrics.themes_by_era(compendium)
    assert all(isinstance(v, dict) for v in by_era.values())
    by_lyricist = lyrics.lyricist_theme_matrix(compendium)
    assert "Robert Hunter" in by_lyricist


def test_reviews_views(compendium):
    per_show = reviews.reviews_per_show(compendium)
    assert sum(per_show.values()) == len(compendium.reviews)
    by_kind = reviews.sentiment_by_kind(compendium)
    assert all(0.0 <= v <= 1.0 for v in by_kind.values())
    s = reviews.sentiment_summary(compendium)
    assert s["n"] >= 1
    assert 0.0 <= s["mean"] <= 1.0


def test_reviews_empty_summary():
    comp = build_compendium()
    s = reviews.sentiment_summary(comp)
    assert s == {"n": 0, "mean": 0.0, "stdev": 0.0}


def test_personnel_timeline_bars(compendium):
    bars = personnel_timeline.bars(compendium)
    person_slugs = {b.person_slug for b in bars}
    assert "garcia" in person_slugs
    diversity = personnel_timeline.lineup_diversity(compendium)
    # At least one show should have ≥5 active musicians.
    assert max(diversity.values()) >= 5
    # Multi-role merge: Garcia has lead-guitar AND vocals on one interval.
    garcia_bars = [b for b in bars if b.person_slug == "garcia"]
    assert any(len(b.roles) >= 2 for b in garcia_bars)
