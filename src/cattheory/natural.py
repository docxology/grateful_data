"""Natural transformations between Date-indexed functors.

We give one concrete, testable natural transformation:

``η : F_setlist  ⟹  Card ∘ F_setlist``

where ``Card : Set → ℕ`` sends a finite set to its cardinality and ``ℕ`` is
the discrete category of natural numbers under ``≤``. ``η_d`` is the
"cardinality of cumulative setlist at date d" map. The naturality square

::

    F_setlist(d1)  --inclusion-->  F_setlist(d2)
         |                                 |
        η_d1                              η_d2
         v                                 v
    |F_setlist(d1)| ----- ≤ ----->  |F_setlist(d2)|

commutes (in fact strictly) by monotonicity of ``F_setlist``. The check
function below verifies that on every date pair in the seed.
"""

from __future__ import annotations

from ..integration.reconcile import Compendium
from .functors import lineup_functor, setlist_functor


def cardinality_eta(functor: dict[str, frozenset[str]]) -> dict[str, int]:
    """``η_d = |F(d)|``."""
    return {d: len(s) for d, s in functor.items()}


def naturality_square_holds(functor: dict[str, frozenset[str]]) -> bool:
    """The naturality-square check for the cardinality transformation.

    Naturality for ``η : F ⟹ Card ∘ F`` over the date poset reduces to
    ``|F(d1)| ≤ |F(d2)|`` whenever ``d1 ≤ d2``. On sorted date keys,
    consecutive cardinality checks suffice.
    """
    dates = sorted(functor.keys())
    sizes = [len(functor[d]) for d in dates]
    for left, right in zip(sizes, sizes[1:], strict=False):
        if left > right:
            return False
    return True


def setlist_cardinality_transformation(compendium: Compendium) -> dict[str, int]:
    return cardinality_eta(setlist_functor(compendium))


def lineup_cardinality_transformation(compendium: Compendium) -> dict[str, int]:
    return cardinality_eta(lineup_functor(compendium))
