"""Tests for the data-completeness audit (real seed + negative controls)."""

from __future__ import annotations

from datetime import date

import pytest

from src.audit import (
    FULL_CORPUS_SHOW_ESTIMATE,
    IncompleteCompendiumError,
    assert_complete,
    audit_completeness,
)
from src.integration.reconcile import build_compendium
from src.models import Performance, Recording, Show, Venue

# Pinned baseline cardinalities (see ISA Constraints).
EXPECTED = {"shows": 83, "songs": 88, "venues": 25, "people": 14, "performances": 341}


def test_seed_is_fully_complete(compendium):
    report = audit_completeness(compendium)
    assert report.is_complete
    assert report.dangling_total == 0


def test_every_relation_resolves(compendium):
    report = audit_completeness(compendium)
    assert report.shows_missing_venue == ()
    assert report.performed_songs_missing_record == ()
    assert report.shows_without_performances == ()
    assert report.reviews_dangling == ()
    assert report.recordings_dangling == ()
    assert report.recordings_date_mismatch == ()
    assert report.releases_dangling_track_refs == ()
    assert report.citations_bad_url == ()


def test_cardinalities_match_pinned_baseline(compendium):
    report = audit_completeness(compendium)
    assert report.n_shows == EXPECTED["shows"]
    assert report.n_songs == EXPECTED["songs"]
    assert report.n_venues == EXPECTED["venues"]
    assert report.n_people == EXPECTED["people"]
    assert report.n_performances == EXPECTED["performances"]


def test_geo_coverage_is_total(compendium):
    report = audit_completeness(compendium)
    assert report.venues_missing_geo == ()
    assert report.geo_coverage_pct == pytest.approx(100.0)


def test_corpus_scope_archival(archival_compendium, monkeypatch):
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    scope = audit_completeness(archival_compendium).corpus_scope
    assert "archival compendium" in scope
    assert str(FULL_CORPUS_SHOW_ESTIMATE) in scope


def test_corpus_scope_is_honest(compendium, monkeypatch):
    """The report must state scope without over-claiming."""
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "seed")
    report = audit_completeness(compendium)
    scope = report.corpus_scope
    assert "compendium" in scope
    assert str(report.n_shows) in scope
    assert str(FULL_CORPUS_SHOW_ESTIMATE) in scope
    assert "all shows ever" not in scope.lower()


def test_assert_complete_passes_on_seed(compendium):
    report = assert_complete(compendium)
    assert report.is_complete


def test_to_dict_round_trips(compendium):
    d = audit_completeness(compendium).to_dict()
    assert d["is_complete"] is True
    assert d["dangling_total"] == 0
    assert "corpus_scope" in d


def test_reports_lyric_and_review_coverage(compendium):
    report = audit_completeness(compendium)
    assert report.songs_with_lyricist_on_pointer >= 0
    assert report.maximinus_reviews_n >= 0
    assert (
        report.curated_reviews_n == len(compendium.reviews) - report.maximinus_reviews_n
    )
    assert "maximinus_reviews_n" in report.to_dict()
    """Optional dimensions (segues, tour) are reported, never hidden."""
    report = audit_completeness(compendium)
    # seed setlists carry no segue markers — this must be transparent, not 0-hidden
    assert report.n_segue_markers == 0
    assert report.n_shows_with_tour == report.n_shows  # every show has a tour label


# --- negative controls: a broken compendium MUST be flagged --------------


def _broken_show() -> Show:
    return Show(
        slug="1969-01-01@ghost_venue", date=date(1969, 1, 1), venue_slug="ghost_venue"
    )


def test_detects_dangling_venue_and_empty_setlist():
    comp = build_compendium(shows=[_broken_show()])
    report = audit_completeness(comp, geo={})
    assert not report.is_complete
    assert "1969-01-01@ghost_venue" in report.shows_missing_venue
    assert "1969-01-01@ghost_venue" in report.shows_without_performances


def test_detects_dangling_song():
    show = _broken_show()
    perf = Performance(
        show_slug=show.slug, song_slug="ghost_song_xyz", set_number=1, position=1
    )
    comp = build_compendium(shows=[show], performances=[perf])
    report = audit_completeness(comp, geo={})
    assert "ghost_song_xyz" in report.performed_songs_missing_record


def test_assert_complete_raises_on_broken():
    comp = build_compendium(shows=[_broken_show()])
    with pytest.raises(IncompleteCompendiumError) as exc:
        assert_complete(comp, geo={})
    assert exc.value.report.dangling_total > 0


def test_detects_wrong_but_resolving_recording_date():
    """A recording resolving to a show on the WRONG date is caught (not just dangling)."""
    show = Show(
        slug="1980-01-01@ghost_venue", date=date(1980, 1, 1), venue_slug="ghost_venue"
    )
    venue = Venue(
        slug="ghost_venue", name="Ghost", city="Nowhere", state_or_region="ZZ"
    )
    # archive_id encodes 1999-12-31 but the resolved show is 1980-01-01.
    rec = Recording(
        archive_id="gd1999-12-31.sbd.x.1.flac16", show_slug=show.slug, source_type="SBD"
    )
    comp = build_compendium(shows=[show], venues=[venue], recordings=[rec])
    report = audit_completeness(
        comp, geo={"ghost_venue": {"lat": 0, "lon": 0, "region": "West"}}
    )
    assert "gd1999-12-31.sbd.x.1.flac16" in report.recordings_date_mismatch
