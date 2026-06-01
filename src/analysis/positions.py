"""Set-position and encore-frequency analytics.

The convention in our shows.json is that ``set_number`` 1 and 2 are the two
regular sets and the highest ``set_number`` in a show is the encore. We mark
that *operationally* here by finding the max ``set_number`` per show.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from ..integration.reconcile import Compendium


def opener_frequency(compendium: Compendium) -> dict[str, int]:
    """How often each song opened a set (lowest ``position`` in that set).

    The opener is selected by ``min(position)`` per ``(show, set_number)`` —
    symmetric with :func:`closer_frequency`'s ``max`` — so the result is
    correct regardless of the order performances arrive in. (Relying on
    iteration order would silently mislabel openers whenever a source emits
    rows unsorted, or whenever a set has no ``position == 1`` row.)
    """
    first_per_set: dict[tuple[str, int], tuple[int, str]] = {}
    for p in compendium.performances:
        key = (p.show_slug, p.set_number)
        prev = first_per_set.get(key)
        if prev is None or p.position < prev[0]:
            first_per_set[key] = (p.position, p.song_slug)
    counter: Counter[str] = Counter(slug for _pos, slug in first_per_set.values())
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def closer_frequency(compendium: Compendium) -> dict[str, int]:
    """How often each song closed a set (highest position in that set)."""
    last_per_set: dict[tuple[str, int], tuple[int, str]] = {}
    for p in compendium.performances:
        key = (p.show_slug, p.set_number)
        prev = last_per_set.get(key)
        if not prev or p.position > prev[0]:
            last_per_set[key] = (p.position, p.song_slug)
    counter: Counter[str] = Counter(slug for _pos, slug in last_per_set.values())
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def encore_frequency(compendium: Compendium) -> dict[str, int]:
    """How often each song appeared in the highest-numbered set of a show."""
    max_set_per_show: dict[str, int] = defaultdict(int)
    for p in compendium.performances:
        max_set_per_show[p.show_slug] = max(max_set_per_show[p.show_slug], p.set_number)
    counter: Counter[str] = Counter()
    for p in compendium.performances:
        if p.set_number == max_set_per_show[p.show_slug]:
            counter[p.song_slug] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def position_distribution(compendium: Compendium) -> dict[int, int]:
    """Aggregate count of songs appearing at each set-position index."""
    counter: Counter[int] = Counter(p.position for p in compendium.performances)
    return dict(sorted(counter.items()))
