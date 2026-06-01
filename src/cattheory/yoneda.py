"""A representable presheaf over the show category.

For a fixed show ``s``, the contravariant ``Hom(-, s)`` from the show
category lands in ``Set`` and sends each show ``t`` to the set of arrows
``t → s``. In our discrete show category there's exactly one arrow (the
identity) when ``t = s`` and none otherwise; the representable presheaf
collapses to the indicator of equality with ``s``.

The Yoneda lemma in this discrete setting reduces to "natural
transformations from ``Hom(-, s)`` to any presheaf ``P`` are in bijection
with elements of ``P(s)``" — a near-tautology that nevertheless gives us a
canonical embedding of every show into the presheaf category. We expose
that embedding here, build the per-show preimage in spans, and let tests
verify the bijection on the seed.
"""

from __future__ import annotations

from ..integration.reconcile import Compendium


def representable_at(
    show_slug: str, all_show_slugs: tuple[str, ...]
) -> dict[str, frozenset[str]]:
    """``Hom(-, show_slug)`` as a dict keyed by show slug."""
    out: dict[str, frozenset[str]] = {}
    for s in all_show_slugs:
        out[s] = frozenset({f"id_{s}"}) if s == show_slug else frozenset()
    return out


def yoneda_embed(compendium: Compendium) -> dict[str, dict[str, frozenset[str]]]:
    """Embed every show as the corresponding representable presheaf."""
    slugs = tuple(s.slug for s in compendium.shows)
    return {s: representable_at(s, slugs) for s in slugs}


def yoneda_bijection_count(compendium: Compendium) -> int:
    """Degenerate (discrete-Show) Yoneda count: 1 per show, == ``len(shows)``.

    In the discrete Show category every representable collapses to an equality
    indicator, so this is a near-tautology. The *non-degenerate* Yoneda
    statement lives over the ``Date`` poset — see
    :func:`yoneda_lemma_holds_for_setlist`.
    """
    embed = yoneda_embed(compendium)
    return sum(
        1 for s, ps in embed.items() for t, pt in embed.items() if s == t and ps == pt
    )


def representable_at_date(
    day_iso: str, all_days_iso: tuple[str, ...]
) -> dict[str, frozenset[str]]:
    """Covariant representable ``Hom(d, -)`` on the ``Date`` poset.

    Sends each date ``e`` to the singleton arrow set ``{"d->e"}`` when
    ``d ≤ e`` and to the empty set otherwise.
    """
    return {
        e: frozenset({f"{day_iso}->{e}"}) if day_iso <= e else frozenset()
        for e in all_days_iso
    }


def count_yoneda_naturals(
    functor: dict[str, frozenset[str]], day_iso: str, universe: frozenset[str]
) -> int:
    """Count natural transformations ``Hom(d, -) ⟹ F`` over the Date poset.

    A natural transformation assigns to the unique arrow ``d -> e`` (present iff
    ``d ≤ e``) an element of ``F(e)``, and naturality with the inclusion legs
    forces that element to be the *same* element ``x`` at every ``e ≥ d``. Such
    an ``x`` is valid iff ``x ∈ F(e)`` for **all** ``e ≥ d``. We count exactly
    those ``x`` drawn from ``universe`` — this is a real naturality check, not a
    tautology: on a non-monotone functor an ``x ∈ F(d)`` that later drops out is
    correctly rejected, so the count falls below ``|F(d)|``.
    """
    later = [e for e in sorted(functor) if e >= day_iso]
    if not later:
        return 0
    return sum(1 for x in universe if all(x in functor[e] for e in later))


def yoneda_lemma_holds_for_setlist(compendium: Compendium, day_iso: str) -> bool:
    """Verify ``Nat(Hom(d, -), F_setlist) ≅ F_setlist(d)`` on the real corpus.

    The cumulative setlist functor is monotone, so the set of natural
    transformations out of the representable ``Hom(d, -)`` is in bijection with
    the cumulative setlist at ``d`` — "the songs played by date ``d`` *are* the
    natural transformations into the setlist functor." Returns ``True`` when the
    counted naturals equal ``|F_setlist(d)|``.
    """
    from .functors import is_monotone, setlist_functor

    functor = setlist_functor(compendium)
    if day_iso not in functor:
        return False
    # The Yoneda bijection Nat(Hom(d,-), F) ≅ F(d) is claimed only for a genuine
    # (monotone, covariant) functor into Set with inclusion legs. The per-date
    # count below inspects only dates ≥ d, so a non-monotone defect EARLIER than
    # d would otherwise slip through; require monotonicity over the whole poset
    # so a non-functorial F is rejected wherever its defect lies.
    if not is_monotone(functor):
        return False
    universe = functor[max(functor)] if functor else frozenset()
    return count_yoneda_naturals(functor, day_iso, universe) == len(functor[day_iso])
