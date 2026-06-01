"""Reception analytics over the bundled review pointers."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, stdev

from ..integration.reconcile import Compendium


def reviews_per_show(compendium: Compendium) -> dict[str, int]:
    counter: dict[str, int] = defaultdict(int)
    for r in compendium.reviews:
        counter[r.show_slug] += 1
    return dict(sorted(counter.items()))


def sentiment_by_kind(compendium: Compendium) -> dict[str, float]:
    by_kind: dict[str, list[float]] = defaultdict(list)
    for r in compendium.reviews:
        by_kind[r.kind].append(r.sentiment)
    return {kind: mean(vs) for kind, vs in by_kind.items()}


def sentiment_by_kind_summary(
    compendium: Compendium,
) -> dict[str, dict[str, float]]:
    """Per-kind sentiment with support and dispersion.

    Returns ``{kind: {"n", "mean", "stdev"}}`` so a kind backed by one review
    is not presented as equal in weight to one backed by hundreds. ``stdev`` is
    the sample standard deviation, or ``0.0`` for a single-observation kind.
    """
    by_kind: dict[str, list[float]] = defaultdict(list)
    for r in compendium.reviews:
        by_kind[r.kind].append(r.sentiment)
    return {
        kind: {
            "n": float(len(vs)),
            "mean": float(mean(vs)),
            "stdev": float(stdev(vs)) if len(vs) > 1 else 0.0,
        }
        for kind, vs in sorted(by_kind.items())
    }


def sentiment_summary(compendium: Compendium) -> dict[str, float]:
    if not compendium.reviews:
        return {"n": 0, "mean": 0.0, "stdev": 0.0}
    scores = [r.sentiment for r in compendium.reviews]
    return {
        "n": float(len(scores)),
        "mean": float(mean(scores)),
        "stdev": float(stdev(scores)) if len(scores) > 1 else 0.0,
    }
