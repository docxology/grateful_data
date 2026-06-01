"""Tests for supplemental source reconciliation reporting."""

from __future__ import annotations

from datetime import date

from src.integration.reconcile import build_compendium
from src.integration.source_reconciliation import (
    ambiguity_buckets,
    conflict_buckets,
    reconcile_gap_fill,
    source_contribution_counts,
    venue_alias_collision_summary,
)
from src.models import Performance, Show, Venue


def test_performance_counts_by_show():
    from src.integration.source_reconciliation import performance_counts_by_show

    show = Show(slug="1977-05-08@barton", date=date(1977, 5, 8), venue_slug="barton")
    venue = Venue(slug="barton", name="Barton", city="Ithaca", state_or_region="NY")
    perfs = [
        Performance(show_slug=show.slug, song_slug="truckin", set_number=1, position=1),
        Performance(show_slug=show.slug, song_slug="ripple", set_number=1, position=2),
    ]
    comp = build_compendium(shows=[show], venues=[venue], performances=perfs)
    counts = performance_counts_by_show(comp)
    assert counts[show.slug] == 2
    show = Show(
        slug="1977-05-08@barton_hall", date=date(1977, 5, 8), venue_slug="barton_hall"
    )
    venue = Venue(
        slug="barton_hall", name="Barton Hall", city="Ithaca", state_or_region="NY"
    )
    perf = Performance(
        show_slug=show.slug, song_slug="truckin", set_number=1, position=1
    )
    comp = build_compendium(shows=[show], venues=[venue], performances=[perf])
    report = reconcile_gap_fill(
        comp,
        supplemental_label="truckin",
        supplemental_show_slugs={"1977-05-08@barton_hall", "1990-01-01@other"},
        supplemental_perf_count=40,
        shows_with_perf_before=set(),
    )
    assert report.gap_shows_added == 2
    assert report.performed_songs_without_lyric_pointer == 1


def test_reconciliation_extended_review_buckets():
    show = Show(slug="1977-05-08@barton", date=date(1977, 5, 8), venue_slug="barton")
    venue = Venue(slug="barton", name="Barton", city="Ithaca", state_or_region="NY")
    perf = Performance(
        show_slug=show.slug, song_slug="truckin", set_number=1, position=1
    )
    comp = build_compendium(shows=[show], venues=[venue], performances=[perf])

    contributions = source_contribution_counts(
        comp,
        ingest_stats={"recordings_dropped_date": 1},
        sources_used=["gdshowsdb", "truckin"],
    )
    assert contributions["entity_counts"]["shows"] == 1
    assert "gdshowsdb" in contributions["source_layers_used"]

    conflicts = conflict_buckets(
        ingest_stats={"recordings_dropped_date": 1},
        skipped_sources=["setlistfm_gd: SETLISTFM_API_KEY not set"],
    )
    assert conflicts["dropped_or_conflict_counters"]["recordings_dropped_date"] == 1
    assert conflicts["n_skipped_sources"] == 1

    ambiguities = ambiguity_buckets(comp)
    assert ambiguities["performed_songs_without_lyric_pointer"] == 1

    venues = venue_alias_collision_summary(comp)
    assert venues["n_collision_groups"] == 0
