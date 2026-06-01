"""Personnel timeline (Gantt-style) data.

We flatten each person's intervals into a list of bars with start/end dates
and the union of distinct roles they held in that interval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class Bar:
    person_slug: str
    full_name: str
    start: date
    end: date | None
    roles: tuple[str, ...]


def bars(compendium: Compendium) -> tuple[Bar, ...]:
    out: list[Bar] = []
    for p in compendium.people:
        # Group intervals by start/end to merge multi-role bars.
        grouped: dict[tuple[date, date | None], list[str]] = {}
        for start, end, role in p.intervals:
            grouped.setdefault((start, end), []).append(role)
        for (start, end), roles in sorted(grouped.items()):
            out.append(
                Bar(
                    person_slug=p.slug,
                    full_name=p.full_name,
                    start=start,
                    end=end,
                    roles=tuple(sorted(set(roles))),
                )
            )
    return tuple(out)


def lineup_diversity(compendium: Compendium) -> dict[str, int]:
    """For each show date, count the active members.

    Useful as a "ensemble size over time" view independent of cumulative
    growth.
    """
    out: dict[str, int] = {}
    for s in compendium.shows:
        active = sum(1 for p in compendium.people if p.active_on(s.date))
        out[s.date.isoformat()] = active
    return dict(sorted(out.items()))
