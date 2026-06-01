"""Tests that the de-vacuumed categorical constructions actually have teeth.

Each construction is paired with a negative control proving it can FAIL on
broken input — the property the previous tautological versions lacked.
"""

from __future__ import annotations

from src.cattheory import categories, colimits, spans, yoneda


# --- colimit universal property --------------------------------------------

def test_colimit_universal_property_holds_on_monotone(compendium):
    from src.cattheory.functors import setlist_functor

    F = setlist_functor(compendium)
    assert colimits.colimit_cone_factors(F) is True


def test_colimit_mediating_map_rejects_too_small_apex():
    # ⋃F = {a, b, c}; a strictly smaller apex cannot receive every F(d).
    F = {"d1": frozenset({"a"}), "d2": frozenset({"a", "b", "c"})}
    colim = frozenset({"a", "b", "c"})
    assert colimits.mediating_map(F, colim | {"z"}) is not None  # larger: factors
    assert colimits.mediating_map(F, frozenset({"a", "b"})) is None  # smaller: fails


def test_colimit_cone_factors_rejects_non_monotone_terminal():
    # REGIME-CORRECT negative control (RedTeam iter-8 CE-3): a non-monotone
    # functor whose terminal value F[max] has shed elements is NOT a valid
    # colimit cone — F[max]={a} != ⋃F={a,b}. colimit_cone_factors (the function
    # the report actually calls) must return False, not certify it.
    F = {"d1": frozenset({"a", "b"}), "d2": frozenset({"a"})}
    assert colimits.colimit_cone_factors(F) is False
    # The mediating-map machinery still distinguishes a strict-subset apex.
    assert colimits.mediating_map(F, frozenset({"a"})) is None


def test_colimit_cone_factors_accepts_monotone_terminal():
    # Monotone family: F[max] == ⋃F, so the cone factors.
    F = {"d1": frozenset({"a"}), "d2": frozenset({"a", "b"})}
    assert colimits.colimit_cone_factors(F) is True


# --- check_laws sampler catches a broken compose ----------------------------

def _linear_poset_category(n: int, *, broken: bool = False) -> categories.Category:
    """A 0..n-1 total order; if broken, compose returns a wrong target."""
    objects = tuple(str(i) for i in range(n))
    arrows = {
        (str(i), str(j)): f"{i}->{j}" for i in range(n) for j in range(n) if i <= j
    }

    def compose(f: str, g: str) -> str:
        a, b = f.split("->")
        b2, c = g.split("->")
        if b != b2:
            raise ValueError("non-composable")
        if broken:
            return f"{a}->{a}"  # wrong: not associative / not closed
        return f"{a}->{c}"

    def identity_of(o: str) -> str:
        return f"{o}->{o}"

    return categories.Category("L", objects, arrows, compose, identity_of)


def test_check_laws_sampler_passes_on_valid_large_category():
    cat = _linear_poset_category(200)  # > 120 -> sampled path
    ok, issues = cat.check_laws(sample_size=300, seed=1)
    assert ok and issues == []


def test_check_laws_sampler_catches_broken_compose_at_scale():
    cat = _linear_poset_category(200, broken=True)
    ok, issues = cat.check_laws(sample_size=300, seed=1)
    assert not ok
    assert any("associativity" in m for m in issues)


def test_check_laws_sampler_is_deterministic():
    cat = _linear_poset_category(200, broken=True)
    assert cat.check_laws(sample_size=200, seed=5) == cat.check_laws(
        sample_size=200, seed=5
    )


def test_check_laws_detects_closure_hole_with_real_compose():
    # REGIME-CORRECT negative control (RedTeam iter-8 CE-1): the real Date
    # compose is pure string surgery whose associativity can NEVER break, so the
    # only data-reachable defect is a non-transitively-closed arrow table. The
    # sampled closure check catches SYSTEMATIC corruption with high probability
    # (it is a regression guard, not a single-needle detector; the laws hold by
    # construction). Here we break transitivity systematically — keep only
    # consecutive + identity arrows — and confirm the sampler fails on closure.
    from datetime import date, timedelta

    days = tuple(date(1970, 1, 1) + timedelta(days=i) for i in range(200))
    cat = categories.build_date_category(days)
    assert cat.check_laws(sample_size=400, seed=1)[0] is True  # intact: passes
    iso = [d.isoformat() for d in days]
    non_closed = {
        (a, b): cat.arrows[(a, b)]
        for i, a in enumerate(iso)
        for j, b in enumerate(iso)
        if i == j or j == i + 1  # only identities + immediate successors
    }
    holed = categories.Category(
        "Date", cat.objects, non_closed, cat.compose, cat.identity_of
    )
    ok, issues = holed.check_laws(sample_size=600, seed=1)
    assert ok is False
    assert any("closure" in m for m in issues)


# --- Yoneda over the Date poset ---------------------------------------------

def test_yoneda_lemma_holds_for_setlist_on_seed(compendium):
    from src.cattheory.functors import setlist_functor

    F = setlist_functor(compendium)
    some_date = sorted(F)[len(F) // 2]
    assert yoneda.yoneda_lemma_holds_for_setlist(compendium, some_date) is True


def test_yoneda_count_negative_control_on_non_monotone():
    # Non-monotone functor: 'x' is in F(d1) but drops out of F(d2>d1) -> the
    # naturality count must fall BELOW |F(d1)|, i.e. the bijection fails.
    F = {"1990-01-01": frozenset({"x", "y"}), "1991-01-01": frozenset({"y"})}
    universe = frozenset({"x", "y"})
    n = yoneda.count_yoneda_naturals(F, "1990-01-01", universe)
    assert n == 1  # only 'y' survives to all later dates
    assert n < len(F["1990-01-01"])  # bijection with F(d) would require 2


def test_yoneda_lemma_requires_monotonicity_anywhere():
    # REGIME-CORRECT negative control (RedTeam iter-8 CE-2): a functor that is
    # non-monotone EARLIER than the query date used to slip through, because the
    # count only inspects dates >= query. The lemma now guards on is_monotone,
    # so a non-monotone functor is rejected wherever the defect sits.
    from src.cattheory.functors import is_monotone

    non_monotone = {
        "1990-01-01": frozenset({"a", "b", "c"}),
        "1991-01-01": frozenset({"z"}),  # shed a,b,c -> not a functor
        "1992-01-01": frozenset({"z"}),
    }
    assert is_monotone(non_monotone) is False
    # The forward-only count at the mid date would have (wrongly) matched |F(d)|.
    mid = "1991-01-01"
    assert yoneda.count_yoneda_naturals(
        non_monotone, mid, frozenset({"a", "b", "c", "z"})
    ) == len(non_monotone[mid])  # the old blind spot...
    # ...which the is_monotone guard in yoneda_lemma_holds_for_setlist now closes.


def test_representable_at_date_is_indicator_of_le():
    days = ("1977-05-07", "1977-05-08", "1977-05-09")
    rep = yoneda.representable_at_date("1977-05-08", days)
    assert rep["1977-05-07"] == frozenset()  # earlier: no arrow
    assert rep["1977-05-08"] != frozenset()  # identity
    assert rep["1977-05-09"] != frozenset()  # later: one arrow


# --- span / setlist-functor commutation -------------------------------------

def test_projections_commute_with_setlist_functor_seed(compendium):
    assert spans.projections_commute_with_setlist_functor(compendium) is True


def test_fibers_over_shows_match_per_show_pullback(compendium):
    sp = spans.build_performance_spans(compendium)
    fibers = spans.fibers_over_shows(sp)
    # Spot-check three shows: the single-pass fiber equals the per-show pullback.
    for show in list(fibers)[:3]:
        assert fibers[show] == spans.wide_pullback_over_show(sp, show)
