"""Repertoire dynamics: catalogue coverage, song lifespans, era turnover.

These are net-new derivations over existing primitives (no new data):

* :func:`catalog_coverage` — how much of the song *catalogue* actually enters
  the performance record, and how many performed slugs are not in the
  catalogue (segment markers + un-catalogued pieces). A data-quality and
  scope-completeness metric.
* :func:`song_lifespans` — each song's first→last performance span, the
  signature "when did this enter/leave rotation" view of the repertoire.
* :func:`repertoire_turnover` — Jaccard similarity / turnover between the
  performed-song sets of consecutive eras: how much the active repertoire
  churns across the band's stylistic periods.

Repertoire views exclude generic segment markers by default (see
``analysis.markers``); the catalogue/coverage view reports them separately.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..integration.reconcile import Compendium
from . import eras
from .markers import is_segment_marker


@dataclass(frozen=True)
class CatalogCoverage:
    """Coverage of the song catalogue by the performance record."""

    n_catalog: int
    n_performed_in_catalog: int
    n_never_performed: int
    never_performed: tuple[str, ...]
    n_performed_not_in_catalog: int
    performed_not_in_catalog: tuple[str, ...]
    n_segment_markers_performed: int

    @property
    def coverage_pct(self) -> float:
        """Percentage of catalogued songs that were ever performed."""
        if self.n_catalog == 0:
            return 0.0
        return round(100.0 * self.n_performed_in_catalog / self.n_catalog, 2)


def catalog_coverage(compendium: Compendium) -> CatalogCoverage:
    """Split the catalogue into performed / never-performed and flag orphans.

    Segment markers are excluded from the catalogue and from the performed set
    (consistent with the rest of ``analysis.repertoire`` and ``stats``), so the
    coverage percentage is a *song* coverage, not inflated by marker rows that
    happen to exist as catalogue entries. Markers performed are reported
    separately in ``n_segment_markers_performed``.
    """
    catalog_slugs = {s.slug for s in compendium.songs if not is_segment_marker(s.slug)}
    performed_slugs = {
        p.song_slug
        for p in compendium.performances
        if not is_segment_marker(p.song_slug)
    }
    performed_in_catalog = sorted(catalog_slugs & performed_slugs)
    never_performed = sorted(catalog_slugs - performed_slugs)
    performed_not_in_catalog = sorted(performed_slugs - catalog_slugs)
    n_segment_markers = len(
        {p.song_slug for p in compendium.performances if is_segment_marker(p.song_slug)}
    )
    return CatalogCoverage(
        n_catalog=len(catalog_slugs),
        n_performed_in_catalog=len(performed_in_catalog),
        n_never_performed=len(never_performed),
        never_performed=tuple(never_performed),
        n_performed_not_in_catalog=len(performed_not_in_catalog),
        performed_not_in_catalog=tuple(performed_not_in_catalog),
        n_segment_markers_performed=n_segment_markers,
    )


@dataclass(frozen=True)
class SongLifespan:
    """First→last performance span of a song, in years and performance count."""

    song_slug: str
    first_year: int
    last_year: int
    n_performances: int
    debut_era: str

    @property
    def span_years(self) -> int:
        return self.last_year - self.first_year


def song_lifespans(
    compendium: Compendium, *, exclude_segments: bool = True, top_n: int | None = None
) -> tuple[SongLifespan, ...]:
    """Per-song first→last performance span, ordered by debut year then slug.

    Excludes generic segment markers by default. When ``top_n`` is given, only
    the ``top_n`` most-performed qualifying songs are returned (still ordered
    by debut), which is the right input for a readable lifespan figure.
    """
    show_date = {s.slug: s.date for s in compendium.shows}
    years: dict[str, list[int]] = {}
    counts: dict[str, int] = {}
    for p in compendium.performances:
        if exclude_segments and is_segment_marker(p.song_slug):
            continue
        d = show_date.get(p.show_slug)
        if d is None:
            continue
        years.setdefault(p.song_slug, []).append(d.year)
        counts[p.song_slug] = counts.get(p.song_slug, 0) + 1

    slugs = list(years)
    if top_n is not None:
        slugs = sorted(slugs, key=lambda s: (-counts[s], s))[:top_n]

    first_date = {s.slug: s.date for s in compendium.shows}
    lifespans = []
    for slug in slugs:
        ys = years[slug]
        # Debut era is the era of the earliest performance date for this song.
        debut_dates = [
            first_date[p.show_slug]
            for p in compendium.performances
            if p.song_slug == slug and p.show_slug in first_date
        ]
        debut_era = eras.era_of(min(debut_dates)) if debut_dates else "Unknown"
        lifespans.append(
            SongLifespan(
                song_slug=slug,
                first_year=min(ys),
                last_year=max(ys),
                n_performances=counts[slug],
                debut_era=debut_era,
            )
        )
    lifespans.sort(key=lambda ls: (ls.first_year, ls.song_slug))
    return tuple(lifespans)


@dataclass(frozen=True)
class EraTurnover:
    """Repertoire similarity/turnover between two consecutive eras."""

    era_a: str
    era_b: str
    n_songs_a: int
    n_songs_b: int
    shared: int
    jaccard: float
    turnover: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "turnover", round(1.0 - self.jaccard, 4))


def _era_song_sets(
    compendium: Compendium, *, exclude_segments: bool
) -> dict[str, set[str]]:
    show_era = {s.slug: eras.era_of(s.date) for s in compendium.shows}
    sets: dict[str, set[str]] = {name: set() for name, _s, _e in eras.ERAS}
    for p in compendium.performances:
        if exclude_segments and is_segment_marker(p.song_slug):
            continue
        era = show_era.get(p.show_slug)
        if era and era in sets:
            sets[era].add(p.song_slug)
    return sets


def repertoire_turnover(
    compendium: Compendium, *, exclude_segments: bool = True
) -> tuple[EraTurnover, ...]:
    """Jaccard similarity + turnover between each pair of consecutive eras."""
    sets = _era_song_sets(compendium, exclude_segments=exclude_segments)
    order = [name for name, _s, _e in eras.ERAS]
    out: list[EraTurnover] = []
    for a, b in zip(order, order[1:]):
        sa, sb = sets[a], sets[b]
        union = sa | sb
        shared = len(sa & sb)
        jaccard = round(len(sa & sb) / len(union), 4) if union else 0.0
        out.append(
            EraTurnover(
                era_a=a,
                era_b=b,
                n_songs_a=len(sa),
                n_songs_b=len(sb),
                shared=shared,
                jaccard=jaccard,
            )
        )
    return tuple(out)


def repertoire_topn_sensitivity(
    compendium: Compendium,
    *,
    top_n_values: tuple[int, ...] = (25, 50, 100, 200),
    exclude_segments: bool = True,
) -> dict[str, object]:
    """Summarize concentration and era coverage across alternate top-N cuts."""

    from .distributions import concentration_summary

    counts: Counter[str] = Counter()
    show_era = {show.slug: eras.era_of(show.date) for show in compendium.shows}
    era_totals: dict[str, Counter[str]] = {name: Counter() for name, _s, _e in eras.ERAS}
    for perf in compendium.performances:
        if exclude_segments and is_segment_marker(perf.song_slug):
            continue
        counts[perf.song_slug] += 1
        era = show_era.get(perf.show_slug)
        if era in era_totals:
            era_totals[era][perf.song_slug] += 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    total = sum(counts.values())
    rows: list[dict[str, object]] = []
    for top_n in top_n_values:
        selected = ordered[:top_n]
        selected_slugs = {slug for slug, _count in selected}
        selected_total = sum(count for _slug, count in selected)
        summary = concentration_summary([count for _slug, count in selected])
        era_rows = []
        for era_name, _start, _end in eras.ERAS:
            era_count = sum(era_totals[era_name][slug] for slug in selected_slugs)
            era_all = sum(era_totals[era_name].values())
            era_rows.append(
                {
                    "era": era_name,
                    "selected_performances": era_count,
                    "era_performance_share_pct": round(100.0 * era_count / era_all, 2)
                    if era_all
                    else 0.0,
                }
            )
        rows.append(
            {
                "top_n": top_n,
                "n_available": len(selected),
                "selected_performances": selected_total,
                "performance_share_pct": round(100.0 * selected_total / total, 2)
                if total
                else 0.0,
                "gini_within_cut": summary.gini,
                "top_10_share_pct_within_cut": summary.top_10_share_pct,
                "era_coverage": era_rows,
            }
        )

    return {
        "method": "deterministic top-N sensitivity over observed performance counts",
        "exclude_segments": exclude_segments,
        "total_non_segment_performances": total,
        "rows": rows,
    }
