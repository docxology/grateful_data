"""Tests for the category-theoretic interpretation.

Two flavours: the abstract algebraic laws (identity, associativity, functor
laws) on a small dummy category, and laws on the seed compendium (monotonicity
of the cumulative setlist and lineup functors, plus span coherence).
"""

from __future__ import annotations

from datetime import date

import pytest

from src.cattheory import (
    AudioEnrichedHom,
    PerformanceSpan,
    build_date_category,
    build_performance_spans,
    build_show_category,
)
from src.cattheory.categories import Category
from src.cattheory.enriched import make_identity_homs
from src.cattheory.functors import (
    active_lineup_presheaf,
    is_monotone,
    lineup_functor,
    setlist_functor,
)
from src.cattheory.spans import wide_pullback_over_show, wide_pullback_over_song
from src.models import Performance


def test_date_category_satisfies_laws():
    cat = build_date_category((date(1970, 1, 1), date(1975, 6, 1), date(1980, 3, 14)))
    ok, issues = cat.check_laws()
    assert ok, issues
    # The composition rule rejects non-composable arrows
    with pytest.raises(ValueError):
        cat.compose("1970-01-01->1975-06-01", "1980-03-14->1985-01-01")
    assert cat.hom("1970-01-01", "1980-03-14") is not None


def test_show_category_is_discrete(compendium):
    cat = build_show_category(compendium)
    ok, issues = cat.check_laws()
    assert ok, issues
    # Hom-set is the singleton identity on each object
    for o in cat.objects:
        assert cat.hom(o, o) == cat.identity_of(o)
    with pytest.raises(ValueError):
        cat.compose("id_a", "id_b")


def test_check_laws_catches_broken_category():
    objects = ("a", "b")
    arrows = {("a", "a"): "id_a", ("b", "b"): "id_b", ("a", "b"): "f"}

    def bad_compose(f, g):
        if (f, g) == ("id_a", "f"):
            return "WRONG"  # Left-identity law violated.
        return f

    def identity_of(o):
        return f"id_{o}"

    cat = Category(
        name="bad",
        objects=objects,
        arrows=arrows,
        compose=bad_compose,
        identity_of=identity_of,
    )
    ok, issues = cat.check_laws()
    assert not ok
    assert any("identity" in i for i in issues)


def test_setlist_functor_is_monotone_on_seed(compendium):
    F = setlist_functor(compendium)
    assert is_monotone(F)


def test_lineup_functor_is_monotone_on_seed(compendium):
    F = lineup_functor(compendium)
    assert is_monotone(F)


def test_active_lineup_presheaf_is_not_monotone_on_seed(compendium):
    P = active_lineup_presheaf(compendium)
    # Pigpen drops out mid-tour; the active-now view is not monotone — that's
    # the categorically meaningful contrast with lineup_functor.
    assert not is_monotone(P)


def test_active_presheaf_pigpen_witness_pair(compendium):
    """Concrete witness: Pigpen ∈ active before mid-1972, ∉ active after.

    The advisor flagged "non-monotone" as a shape claim that needs a content
    witness — the failure mode is "we said it's not monotone but never named
    the witness pair from real data". Here it is, by data.
    """
    P = active_lineup_presheaf(compendium)
    before_keys = [k for k in P if k < "1972-06-17"]
    after_keys = [k for k in P if k > "1972-06-17"]
    assert before_keys and after_keys
    assert "pigpen" in P[before_keys[-1]]
    assert "pigpen" not in P[after_keys[0]]
    # And the cumulative lineup_functor still holds Pigpen after he leaves.
    F = lineup_functor(compendium)
    assert "pigpen" in F[after_keys[0]]


def test_lineup_functor_monotone_witness_pair(compendium):
    """Concrete monotone witness for lineup_functor.

    The cumulative roster never shrinks: there exist dates d1 < d2 such that
    F(d1) ⊆ F(d2) strictly when the band gains a member between them.
    Brent Mydland joined in 1979-04; we look at a date before vs after.
    """
    F = lineup_functor(compendium)
    pre = [k for k in F if k < "1979-04-22"]
    post = [k for k in F if k > "1979-04-22"]
    assert pre and post
    assert F[pre[-1]].issubset(F[post[0]])
    assert "mydland" in F[post[0]]
    assert "mydland" not in F[pre[-1]]


def test_wide_pullback_over_show_equals_setlist(compendium):
    """Concrete diagram check: fiber over a show equals that show's setlist.

    For each show in the seed, the multiset returned by
    ``wide_pullback_over_show`` matches the setlist obtained by walking the
    performance table in canonical order. This binds the categorical prose
    claim to the data.
    """
    from src.cattheory.spans import build_performance_spans, wide_pullback_over_show

    spans = build_performance_spans(compendium)
    for show in compendium.shows[:5]:
        fiber = wide_pullback_over_show(spans, show.slug)
        direct = tuple(
            p.song_slug
            for p in sorted(
                (p for p in compendium.performances if p.show_slug == show.slug),
                key=lambda x: (x.set_number, x.position),
            )
        )
        assert fiber == direct, f"fiber/setlist mismatch on {show.slug}"


def test_performance_span_pullback_diagram_commutes_on_seed(compendium):
    """Diagram-commutativity witness for the performance-as-span construction.

    For any show s and any performance p with π_show(p) = s, the pair
    (s, π_song(p)) is exactly the (show, song) join of that performance.
    """
    spans = build_performance_spans(compendium)
    s0 = compendium.shows[0].slug
    fiber = [sp for sp in spans if sp.show_slug == s0]
    assert fiber, "every show in the seed has at least one performance"
    for sp in fiber:
        # Both projections, composed against the original Performance, agree.
        assert sp.apex.show_slug == sp.projection_to_show() == s0
        assert sp.apex.song_slug == sp.projection_to_song()


def test_is_monotone_rejects_non_monotone():
    bad = {"2000-01-01": frozenset({"a"}), "2001-01-01": frozenset()}
    assert not is_monotone(bad)


def test_performance_spans_round_trip(compendium):
    spans = build_performance_spans(compendium)
    assert len(spans) == len(compendium.performances)
    show_slug = compendium.shows[0].slug
    songs_at_show = wide_pullback_over_show(spans, show_slug)
    assert all(
        p.song_slug in songs_at_show
        for p in compendium.performances
        if p.show_slug == show_slug
    )
    if compendium.songs:
        # Pick a song that actually appears in performances
        any_perf = compendium.performances[0]
        shows = wide_pullback_over_song(spans, any_perf.song_slug)
        assert any_perf.show_slug in shows


def test_performance_span_projections():
    p = Performance(show_slug="s", song_slug="x", set_number=1, position=1)
    span = PerformanceSpan.of(p)
    assert span.projection_to_show() == "s"
    assert span.projection_to_song() == "x"


def test_audio_enriched_hom_constraints():
    pa = Performance(show_slug="s1", song_slug="dark_star", set_number=1, position=1)
    pb = Performance(show_slug="s2", song_slug="dark_star", set_number=1, position=1)
    hom = AudioEnrichedHom(perf_a=pa, perf_b=pb, weight=0.73)
    assert not hom.is_identity_at(pa)
    identity = AudioEnrichedHom(perf_a=pa, perf_b=pa, weight=1.0)
    assert identity.is_identity_at(pa)
    with pytest.raises(ValueError):
        AudioEnrichedHom(perf_a=pa, perf_b=pb, weight=1.5)
    with pytest.raises(ValueError):
        pc = Performance(show_slug="s2", song_slug="ripple", set_number=1, position=1)
        AudioEnrichedHom(perf_a=pa, perf_b=pc, weight=0.5)


def test_make_identity_homs(compendium):
    homs = make_identity_homs(compendium.performances[:5])
    assert len(homs) == 5
    for h in homs:
        assert h.weight == 1.0
        assert h.is_identity_at(h.perf_a)
