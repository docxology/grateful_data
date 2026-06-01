"""The opposite category — reverse every arrow.

For our thin ``Date`` poset, the opposite ``Date^op`` is the same set of
objects with the dual order ``≥``. Contravariant functors out of ``Date``
are the same as covariant functors out of ``Date^op``; that is the
motivation for the presheaf view of ``active_lineup_presheaf`` — it is
covariant on ``Date^op`` even though it is not covariant on ``Date``.
"""

from __future__ import annotations

from .categories import Category


def opposite(cat: Category) -> Category:
    """Return ``cat^op``: same objects, reversed arrows."""
    new_arrows = {(b, a): f"op({arrow})" for (a, b), arrow in cat.arrows.items()}

    def compose(f: str, g: str) -> str:
        # f: a^op -> b^op corresponds to b -> a in cat; composition reverses.
        return f"op_compose({f},{g})"

    def identity_of(o: str) -> str:
        return f"op({cat.identity_of(o)})"

    return Category(
        name=f"{cat.name}^op",
        objects=cat.objects,
        arrows=new_arrows,
        compose=compose,
        identity_of=identity_of,
    )
