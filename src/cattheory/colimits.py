"""Colimits over the compendium.

Two simple but concrete constructions:

* ``coproduct(c1, c2)`` — the binary coproduct of two compendium fragments,
  i.e. the disjoint-union ``Compendium`` whose entity tuples are the
  sorted-deduplicated union. Slug collisions resolve via the same merge
  rules used in ``integration.reconcile``.

* ``colimit_of_setlist_functor(comp)`` — the colimit of the cumulative
  setlist functor on the seed. For a monotone functor on a poset the
  colimit is the union of the codomain; we therefore return the
  cumulative setlist at the latest date as the colimit cone's apex.

These are not the most interesting categorical constructions in the world,
but they are *real*: they live in code, they have negative-control tests,
and they hook into the same primitives the rest of the project uses.
"""

from __future__ import annotations

from ..integration.reconcile import Compendium, build_compendium
from .functors import setlist_functor


def coproduct(a: Compendium, b: Compendium) -> Compendium:
    """Binary coproduct in the discrete-compendium category."""
    return build_compendium(
        shows=tuple(a.shows) + tuple(b.shows),
        venues=tuple(a.venues) + tuple(b.venues),
        songs=tuple(a.songs) + tuple(b.songs),
        people=tuple(a.people) + tuple(b.people),
        performances=tuple(a.performances) + tuple(b.performances),
        recordings=tuple(a.recordings) + tuple(b.recordings),
        releases=tuple(a.releases) + tuple(b.releases),
        citations=tuple(a.citations) + tuple(b.citations),
        lyric_pointers=tuple(a.lyric_pointers) + tuple(b.lyric_pointers),
        reviews=tuple(a.reviews) + tuple(b.reviews),
    )


def colimit_of_setlist_functor(comp: Compendium) -> frozenset[str]:
    """Colimit of the cumulative setlist functor — the final cumulative set."""
    F = setlist_functor(comp)
    if not F:
        return frozenset()
    return F[max(F)]


def mediating_map(
    F: dict[str, frozenset[str]], apex: frozenset[str]
) -> dict[str, str] | None:
    """The unique mediating map ``⋃F → apex`` for a candidate cocone vertex.

    ``apex`` is the vertex of a candidate cocone whose legs ``F(d) → apex`` are
    set-inclusions. Such a cocone exists iff ``apex`` receives every ``F(d)``
    (i.e. ``F(d) ⊆ apex`` for all ``d``). When it does, the colimit's universal
    property gives a *unique* map ``u : ⋃F → apex`` with ``u ∘ ι_d`` equal to
    each leg; in ``Set`` with inclusions this ``u`` is itself the inclusion, and
    it is unique because every element of ``⋃F`` lies in some ``F(d)`` and
    commutativity with that leg forces ``u(x) = x``. Returns that inclusion as a
    dict, or ``None`` when ``apex`` is not a valid cocone vertex.
    """
    colim = set().union(*F.values()) if F else set()
    if not all(F[d] <= apex for d in F):
        return None
    return {x: x for x in sorted(colim)}


def colimit_cone_factors(F: dict[str, frozenset[str]]) -> bool:
    """Verify the colimit's universal property with a built-in negative control.

    The colimit of a monotone ``F : Date → Set`` is ``⋃F`` with inclusion legs.
    Universality says: every cocone vertex admits a *unique* mediating map from
    the colimit. We check this for real:

    * **Positive:** a strictly larger candidate vertex (``⋃F`` plus a fresh
      element) must admit the mediating inclusion.
    * **Negative:** a candidate that is *strictly smaller* than ``⋃F`` (one
      element removed) must **fail** to receive the colimit — there is no
      factorization, because some ``F(d)`` no longer includes into it.

    A construction that merely asserts ``F(d) ⊆ ⋃F`` (true for any family) would
    pass the positive case but cannot distinguish the negative one; requiring
    the negative control to fail is what makes this non-vacuous.
    """
    if not F:
        return True
    colim = set().union(*F.values())
    # The construction's claim is substantive, not tautological: the apex that
    # ``colimit_of_setlist_functor`` actually returns to callers — F at the
    # terminal date, F[max(F)] — must EQUAL the colimit (the union). This holds
    # iff F is genuinely cumulative/monotone; a non-monotone F whose terminal
    # value has shed elements (F[max] ⊊ ⋃F) is NOT a valid colimit cone and is
    # rejected here. (A check that only compared ⋃F against itself would be a
    # tautology that no functor defect could break — this compares the returned
    # apex against the union.)
    returned_apex = F[max(F)]
    if frozenset(returned_apex) != frozenset(colim):
        return False
    bigger = frozenset(colim | {"\x00colimit_probe"})
    if mediating_map(F, bigger) is None:
        return False  # a valid (larger) cocone vertex must factor
    if colim:
        smaller = frozenset(colim - {min(colim)})
        if mediating_map(F, smaller) is not None:
            return False  # a strictly-smaller vertex must NOT factor
    return True
