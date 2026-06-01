"""Era partitioning + density analytics.

The Grateful Dead's career splits naturally into well-known eras whose
boundaries are determined by personnel and stylistic transitions:

* ``Primal``       — 1965-12-04 → 1971-02-18 (Pigpen-led; pre-Wharf-Rat-era)
* ``Europe 72``    — 1971-02-19 → 1973-03-08 (Pigpen's exit, Keith Godchaux in)
* ``Wall of Sound``— 1973-03-09 → 1974-10-20 (peak gear era)
* ``Hiatus->Return``— 1974-10-21 → 1979-02-17 (hiatus + Mickey Hart return)
* ``Brent Era``    — 1979-02-18 → 1990-07-26 (Brent Mydland)
* ``Vince+Bruce``  — 1990-07-27 → 1995-08-09 (Welnick + Hornsby through final show)
"""

from __future__ import annotations

from datetime import date

from ..integration.reconcile import Compendium

ERAS: tuple[tuple[str, date, date], ...] = (
    ("Primal", date(1965, 12, 4), date(1971, 2, 18)),
    ("Europe 72", date(1971, 2, 19), date(1973, 3, 8)),
    ("Wall of Sound", date(1973, 3, 9), date(1974, 10, 20)),
    ("Hiatus->Return", date(1974, 10, 21), date(1979, 2, 17)),
    ("Brent", date(1979, 2, 18), date(1990, 7, 26)),
    ("Vince+Bruce", date(1990, 7, 27), date(1995, 8, 9)),
)


def era_of(day: date) -> str:
    for name, start, end in ERAS:
        if start <= day <= end:
            return name
    return "Unknown"


def shows_by_era(compendium: Compendium) -> dict[str, int]:
    counter: dict[str, int] = {name: 0 for name, _s, _e in ERAS}
    for s in compendium.shows:
        counter[era_of(s.date)] = counter.get(era_of(s.date), 0) + 1
    return counter


def performances_by_era(compendium: Compendium) -> dict[str, int]:
    show_era = {s.slug: era_of(s.date) for s in compendium.shows}
    counter: dict[str, int] = {name: 0 for name, _s, _e in ERAS}
    for p in compendium.performances:
        era = show_era.get(p.show_slug)
        if era:
            counter[era] = counter.get(era, 0) + 1
    return counter


def year_month_density(compendium: Compendium) -> dict[tuple[int, int], int]:
    """Return a (year, month) → show-count map covering the active years."""
    out: dict[tuple[int, int], int] = {}
    for s in compendium.shows:
        key = (s.date.year, s.date.month)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))
