"""Audio-feature enrichment of the performance category.

Following the ``fifteen-songs-dataset`` precedent (Grateful Dead live, 2617
soundboard versions of 15 songs), we treat each pair of performances of the
*same song* as carrying a similarity weight in ``[0, 1]``. The category whose
objects are performances and whose hom-objects are these weights is *enriched
over* the unit-interval monoid ``([0, 1], max, 0)``.

We do not bundle audio. We bundle the abstraction: a class that holds
``(perf_a, perf_b, weight)`` triples plus the law-check that weights are in
``[0, 1]`` and ties — performances of the same song to themselves — carry
weight ``1.0`` (the identity in the enrichment).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import Performance


@dataclass(frozen=True)
class AudioEnrichedHom:
    """An enriched hom triple between two performances of the same song."""

    perf_a: Performance
    perf_b: Performance
    weight: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(
                f"AudioEnrichedHom.weight {self.weight} must lie in [0, 1]"
            )
        if self.perf_a.song_slug != self.perf_b.song_slug:
            raise ValueError(
                "Enriched homs only exist between performances of the same song"
            )

    def is_identity_at(self, perf: Performance) -> bool:
        """Identity arrow predicate at ``perf`` in the enrichment."""
        return self.perf_a == perf and self.perf_b == perf and self.weight == 1.0


def make_identity_homs(perfs: Iterable[Performance]) -> tuple[AudioEnrichedHom, ...]:
    """Build the canonical identity homs (one per performance, weight 1.0)."""
    return tuple(AudioEnrichedHom(p, p, 1.0) for p in perfs)
