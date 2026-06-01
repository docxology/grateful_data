"""Archival-tier GROUND-TRUTH bindings (RedTeam iter-8 oracle fix).

The pre-existing archival tests assert only THRESHOLDS (``>= 2000`` shows, etc.),
so a silently-corrupted value — e.g. ``top_song_count: 99999`` — shipped green.
These tests pin the *actual* values of the committed archival snapshot, so any
drift in the data, the analysis, or the report is caught. They run only when
``data/archival/`` is present (the snapshot is committed for this project) and
are exact, not threshold, assertions.

If the committed archival snapshot is deliberately refreshed, update these
pins in the same commit — that is the point: the manuscript's headline numbers
are now bound to ground truth, not free to drift.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis import repertoire, stats, transitions
from src.analysis.geo import load_geo
from src.analysis.venues import venue_duplication_report
from src.audit import audit_completeness
from src.cattheory.colimits import colimit_cone_factors
from src.cattheory.functors import lineup_functor, setlist_functor
from src.cattheory.spans import projections_commute_with_setlist_functor
from src.cattheory.yoneda import yoneda_lemma_holds_for_setlist

_ARCHIVAL_DIR = Path(__file__).resolve().parent.parent / "data" / "archival"


def _archival_geo() -> dict:
    """Geo sidecar for the archival tier (load_geo() defaults to seed off-env)."""
    return load_geo(_ARCHIVAL_DIR)


def test_archival_top_song_value(archival_compendium):
    s = stats.compute(archival_compendium)
    slug, count = s.top_songs[0]
    assert slug == "playing_in_the_band"  # NOT a segment marker
    assert count == 752  # pinned value, not a >= threshold


def test_archival_segment_marker_counts(archival_compendium):
    s = stats.compute(archival_compendium)
    markers = dict(s.segment_marker_counts)
    assert markers == {"drums": 1777, "feedback": 76, "jam": 317, "space": 1247}


def test_archival_top_line_cardinalities(archival_compendium):
    r = audit_completeness(
        archival_compendium, geo=_archival_geo(), tier="archival"
    )
    assert (r.n_shows, r.n_performances, r.n_venues, r.n_songs) == (
        3341,
        40757,
        912,
        645,
    )
    assert r.geo_coverage_pct == 100.0
    assert r.dangling_total == 0


def test_archival_empty_setlist_count_is_bound(archival_compendium):
    # The 282 empty-setlist shows must be surfaced as a pinned number, not
    # folded into is_complete and forgotten (RedTeam iter-8 CE on audit).
    r = audit_completeness(
        archival_compendium, geo=_archival_geo(), tier="archival"
    )
    assert r.n_shows_without_performances == 282
    assert r.is_complete is True  # referential completeness holds despite the 282


def test_archival_catalog_coverage(archival_compendium):
    cov = repertoire.catalog_coverage(archival_compendium)
    assert cov.coverage_pct == 69.42
    assert cov.n_never_performed == 196


def test_archival_venue_duplication(archival_compendium):
    vd = venue_duplication_report(archival_compendium)
    assert vd.n_venues_collapsed == 20
    assert vd.n_venues_after_canonicalization == 892
    assert vd.n_ambiguous_same_date_collisions == 311


def test_archival_date_poset_objects(archival_compendium):
    assert len({s.date for s in archival_compendium.shows}) == 2312


def test_archival_category_theory_values(archival_compendium):
    F = setlist_functor(archival_compendium)
    L = lineup_functor(archival_compendium)
    assert len(F[max(F)]) == 449  # cumulative setlist cardinality at terminal date
    assert len(L[max(L)]) == 14
    assert colimit_cone_factors(F) is True
    assert projections_commute_with_setlist_functor(archival_compendium) is True
    assert (
        yoneda_lemma_holds_for_setlist(archival_compendium, sorted(F)[len(F) // 2])
        is True
    )


def test_archival_transition_fdr_significance(archival_compendium):
    # Pin the FDR-controlled count (deterministic for the fixed seed) AND assert
    # the canonical segue survives — binds the corrected number, not the
    # uncorrected one.
    summary = transitions.transition_significance_summary(
        archival_compendium, min_support=20, n_permutations=200, fdr_q=0.05, seed=0
    )
    assert summary["n_fdr_significant"] == 1533
    assert summary["n_uncorrected"] == 2284
    assert summary["n_candidates"] == 7639
    top = summary["significant"][0]
    assert (top[0], top[1]) == ("drums", "space")


def test_archival_transition_fdr_kills_null_structure(archival_compendium):
    # NEGATIVE CONTROL (RedTeam iter-8 V-STATS): shuffle song labels across all
    # performances to destroy ordering structure; FDR-controlled count must be 0
    # even though the uncorrected screen still flags ~5% by chance.
    import numpy as np

    from src.integration.reconcile import Compendium
    from src.models import Performance

    a = archival_compendium
    rng = np.random.default_rng(1)
    shuffled = list(rng.permutation([p.song_slug for p in a.performances]))
    null_perfs = tuple(
        Performance(
            show_slug=p.show_slug,
            song_slug=shuffled[i],
            set_number=p.set_number,
            position=p.position,
        )
        for i, p in enumerate(a.performances)
    )
    null = Compendium(
        shows=a.shows,
        venues=a.venues,
        songs=a.songs,
        people=a.people,
        performances=null_perfs,
        recordings=a.recordings,
        releases=a.releases,
        citations=a.citations,
        lyric_pointers=a.lyric_pointers,
        reviews=a.reviews,
    )
    summary = transitions.transition_significance_summary(
        null, min_support=20, n_permutations=200, fdr_q=0.05, seed=0
    )
    assert summary["n_fdr_significant"] == 0  # FDR controls false positives to 0
    assert summary["n_uncorrected"] > 100  # ...while uncorrected still flags noise
