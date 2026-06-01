"""Functors from the ``Date`` category into ``Set``.

For testability we represent the codomain as ``frozenset[str]`` (a small
finite slice of the power-set functor) and a functor as a dict
``object_id -> frozenset``. The functor laws we check:

* ``F(id_d) = id_{F(d)}`` — trivially true because identities on a discrete
  ``Set`` slice are identities on the underlying frozenset.
* ``F(g ∘ f) = F(g) ∘ F(f)`` — in our chosen target ``Set``, both
  ``F(f)`` and ``F(g)`` are inclusions (no actual data motion), so this
  composition holds whenever ``F`` is monotone in the poset.

We verify monotonicity for the setlist functor (a song played in earlier shows
remains in the cumulative setlist) and for the lineup functor (we treat the
cumulative roster as the codomain, so lineup_functor(date) returns the set of
people active *at or before* that date).
"""

from __future__ import annotations

from datetime import date as _date

from ..integration.reconcile import Compendium


def setlist_functor(compendium: Compendium) -> dict[str, frozenset[str]]:
    """Cumulative setlist by date: songs ever played up to and including ``d``."""
    by_date: dict[_date, set[str]] = {}
    show_to_date = {s.slug: s.date for s in compendium.shows}
    for p in compendium.performances:
        d = show_to_date.get(p.show_slug)
        if d is None:
            continue
        by_date.setdefault(d, set()).add(p.song_slug)
    cumulative: set[str] = set()
    out: dict[str, frozenset[str]] = {}
    for d in sorted(by_date):
        cumulative |= by_date[d]
        out[d.isoformat()] = frozenset(cumulative)
    return out


def lineup_functor(compendium: Compendium) -> dict[str, frozenset[str]]:
    """Cumulative active-or-historic roster by date.

    The codomain of this functor is the *cumulative* roster: everyone who has
    been in the band at any point on or before ``d``. That makes the functor
    monotone on the ``Date`` poset, which is the categorically clean
    statement. Use :func:`active_lineup_presheaf` for the non-monotone
    "who is in the band right now" view.
    """
    dates = sorted({s.date for s in compendium.shows})
    cumulative: set[str] = set()
    out: dict[str, frozenset[str]] = {}
    for d in dates:
        for p in compendium.people:
            if any(start <= d for start, _end, _role in p.intervals):
                cumulative.add(p.slug)
        out[d.isoformat()] = frozenset(cumulative)
    return out


def active_lineup_presheaf(compendium: Compendium) -> dict[str, frozenset[str]]:
    """The "who is in the band right now" view.

    This is *not* monotone — Pigpen leaves the active set in 1972, Constanten
    in 1970. As a presheaf on the poset it's still well-defined; as a
    covariant functor into ``Set`` it would fail the functor laws.
    """
    dates = sorted({s.date for s in compendium.shows})
    out: dict[str, frozenset[str]] = {}
    for d in dates:
        active = {p.slug for p in compendium.people if p.active_on(d)}
        out[d.isoformat()] = frozenset(active)
    return out


def is_monotone(functor: dict[str, frozenset[str]]) -> bool:
    """Check that the functor maps ≤ in ``Date`` to ⊆ in ``Set``.

    On a totally ordered key set, checking consecutive dates is sufficient
    (transitivity of ``⊆``); this keeps archival-scale corpora tractable.
    """
    keys = sorted(functor.keys())
    for a, b in zip(keys, keys[1:], strict=False):
        if not functor[a].issubset(functor[b]):
            return False
    return True
