"""Tests for seed → gdshowsdb show slug remapping."""

from __future__ import annotations

from datetime import date

from src.ingest.remap_curated_refs import remap_reviews_and_recordings
from src.models import Recording, Review, Show


def test_remap_barton_hall_seed_slug() -> None:
    shows = (
        Show(
            slug="1977-05-08@barton_hall_cornell_university_ithaca",
            date=date(1977, 5, 8),
            venue_slug="barton_hall_cornell_university_ithaca",
        ),
    )
    reviews = [
        Review(
            show_slug="1977-05-08@barton_hall_ithaca",
            author="fan",
            sentiment=1.0,
            summary="great show",
            source_url="https://example.com",
            kind="fan",
        )
    ]
    remapped, _ = remap_reviews_and_recordings(shows, reviews, [])
    assert remapped[0].show_slug == shows[0].slug


def test_remap_winterland_arena_alias() -> None:
    shows = (
        Show(
            slug="1974-10-20@winterland_san_francisco",
            date=date(1974, 10, 20),
            venue_slug="winterland_san_francisco",
        ),
    )
    recordings = [
        Recording(
            archive_id="gd1974-10-20.test",
            show_slug="1974-10-20@winterland_arena_san_francisco",
            url="https://archive.org/details/gd1974-10-20.test",
            source_type="SBD",
        )
    ]
    _, remapped_recs = remap_reviews_and_recordings(shows, [], recordings)
    assert remapped_recs[0].show_slug == shows[0].slug
