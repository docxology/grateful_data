"""Tests for the venue-alias layer and the (non-mutating) duplication report."""

from __future__ import annotations

from datetime import date

from src.analysis.venues import venue_duplication_report, venue_identity_review
from src.integration.aliases import (
    VENUE_ALIAS_MAP,
    canonicalize_venue_slug,
)
from src.integration.reconcile import Compendium
from src.models import Performance, Show, Venue


# --- alias map: collapses known dupes, NEVER over-collapses --------------------

def test_known_variants_collapse_to_canonical():
    assert canonicalize_venue_slug("oakland_coliseum_oakland") == (
        "oakland_coliseum_arena_oakland"
    )
    assert canonicalize_venue_slug("spectrum_philadelphia") == (
        "the_spectrum_philadelphia"
    )
    assert canonicalize_venue_slug("winterland_san_francisco") == (
        "winterland_arena_san_francisco"
    )
    assert canonicalize_venue_slug("nassau_coliseum_uniondale") == (
        "nassau_veterans_memorial_coliseum_uniondale"
    )


def test_negative_controls_stay_distinct():
    # Distinct venues must NEVER collapse together.
    distinct = [
        "fillmore_west_san_francisco",
        "fillmore_east_new_york",
        "fillmore_auditorium_san_francisco",
        "oakland_coliseum_stadium_oakland",  # outdoor stadium != indoor arena
        "oakland_auditorium_oakland",  # pre-1984 name, not folded into Kaiser
        "felt_forum_madison_square_garden_new_york",  # a room, != MSG main
    ]
    canon = {canonicalize_venue_slug(s) for s in distinct}
    assert len(canon) == len(distinct)  # all still distinct
    # Specifically the arena/stadium split holds.
    assert canonicalize_venue_slug("oakland_coliseum_stadium_oakland") != (
        "oakland_coliseum_arena_oakland"
    )


def test_canonical_targets_are_fixed_points():
    # Applying the map twice equals applying it once (targets map to themselves).
    for src in VENUE_ALIAS_MAP:
        once = canonicalize_venue_slug(src)
        assert canonicalize_venue_slug(once) == once


def test_unknown_slug_is_identity():
    assert canonicalize_venue_slug("barton_hall_ithaca") == "barton_hall_ithaca"


# --- non-mutating report -------------------------------------------------------

def _two_spelling_compendium() -> Compendium:
    # One concert per date, but listed under two venue spellings on 1972-01-02.
    shows = (
        Show(slug="1972-01-02@winterland_san_francisco", date=date(1972, 1, 2),
             venue_slug="winterland_san_francisco"),
        Show(slug="1972-01-02@winterland_arena_san_francisco", date=date(1972, 1, 2),
             venue_slug="winterland_arena_san_francisco"),
    )
    venues = (
        Venue(slug="winterland_san_francisco", name="Winterland", city="SF",
              state_or_region="CA"),
        Venue(slug="winterland_arena_san_francisco", name="Winterland Arena",
              city="SF", state_or_region="CA"),
    )
    perfs = (
        Performance(show_slug="1972-01-02@winterland_san_francisco",
                    song_slug="dark_star", set_number=1, position=1),
        Performance(show_slug="1972-01-02@winterland_arena_san_francisco",
                    song_slug="sugar_magnolia", set_number=1, position=1),
    )
    return Compendium(shows=shows, venues=venues, performances=perfs)


def test_report_detects_collapse_and_collision():
    rep = venue_duplication_report(_two_spelling_compendium())
    assert rep.n_venue_slugs == 2
    assert rep.n_venues_after_canonicalization == 1  # both -> canonical
    assert rep.n_venues_collapsed == 1
    assert rep.n_ambiguous_same_date_collisions == 1  # same date, same canon venue
    # Near-disjoint setlists -> low jaccard -> why we do NOT auto-merge.
    assert rep.mean_collision_setlist_jaccard < 0.5


def test_report_is_noop_clean_on_seed(compendium):
    rep = venue_duplication_report(compendium)
    assert rep.n_alias_slugs_present == 0
    assert rep.n_venues_collapsed == 0
    assert rep.n_ambiguous_same_date_collisions == 0


def test_venue_identity_review_documents_aliases_and_negative_controls(compendium):
    review = venue_identity_review(compendium)
    assert review["summary"]["n_venue_slugs"] == len(compendium.venues)
    assert review["alias_decisions"]
    assert all(row["decision_status"] == "reviewed-collapse" for row in review["alias_decisions"])
    controls = review["negative_controls"]
    assert controls
    assert all(row["preserved_distinct"] for row in controls)
