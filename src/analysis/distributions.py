"""Distribution and concentration statistics over the compendium.

These helpers keep descriptive statistical claims out of plotting code. The
outputs are deliberately modest: robust percentiles, mean/stdev for context,
and simple concentration measures that describe skew without implying causes.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from math import sqrt

import numpy as np

from ..integration.reconcile import Compendium
from .markers import is_segment_marker


@dataclass(frozen=True)
class NumericSummary:
    """Compact summary of a numeric distribution."""

    n: int
    minimum: float
    p25: float
    median: float
    mean: float
    p75: float
    p90: float
    maximum: float
    stdev: float
    iqr: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class ConcentrationSummary:
    """Pareto/Gini summary for non-negative counts."""

    n_items: int
    total: int
    gini: float
    top_10_share_pct: float
    n_for_50_pct: int
    pct_items_for_50_pct: float
    n_for_80_pct: int
    pct_items_for_80_pct: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class PerformanceDistribution:
    """Show-level performance-row distribution."""

    per_show: NumericSummary
    n_zero_performance_shows: int

    def to_dict(self) -> dict[str, object]:
        return {
            "per_show": self.per_show.to_dict(),
            "n_zero_performance_shows": self.n_zero_performance_shows,
        }


@dataclass(frozen=True)
class BootstrapInterval:
    """Fixed-seed bootstrap interval for one concentration statistic."""

    point: float
    low: float
    high: float
    confidence: float
    n_resamples: int
    seed: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class BootstrapConcentrationSummary:
    """Bootstrap uncertainty for Gini and top-decile concentration."""

    gini: BootstrapInterval
    top_10_share_pct: BootstrapInterval

    def to_dict(self) -> dict[str, object]:
        return {
            "gini": self.gini.to_dict(),
            "top_10_share_pct": self.top_10_share_pct.to_dict(),
        }


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolated percentile for an already sorted list."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return round(sorted_values[0], 4)
    rank = (len(sorted_values) - 1) * pct
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return round(sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac, 4)


def summarize_numeric(values: list[int] | tuple[int, ...]) -> NumericSummary:
    """Return robust descriptive statistics for a non-empty or empty sequence."""
    if not values:
        return NumericSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    vals = sorted(float(v) for v in values)
    n = len(vals)
    mean = sum(vals) / n
    variance = sum((v - mean) ** 2 for v in vals) / n
    p25 = _percentile(vals, 0.25)
    p75 = _percentile(vals, 0.75)
    return NumericSummary(
        n=n,
        minimum=round(vals[0], 4),
        p25=p25,
        median=_percentile(vals, 0.5),
        mean=round(mean, 4),
        p75=p75,
        p90=_percentile(vals, 0.9),
        maximum=round(vals[-1], 4),
        stdev=round(sqrt(variance), 4),
        iqr=round(p75 - p25, 4),
    )


def _gini(values: list[int]) -> float:
    """Gini coefficient for non-negative counts."""
    vals = sorted(v for v in values if v >= 0)
    if not vals:
        return 0.0
    total = sum(vals)
    if total == 0:
        return 0.0
    n = len(vals)
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return round((2 * weighted) / (n * total) - (n + 1) / n, 4)


def _items_for_share(sorted_desc: list[int], share: float) -> int:
    total = sum(sorted_desc)
    if total <= 0:
        return 0
    running = 0
    for idx, value in enumerate(sorted_desc, start=1):
        running += value
        if running / total >= share:
            return idx
    return len(sorted_desc)


def concentration_summary(values: list[int] | tuple[int, ...]) -> ConcentrationSummary:
    """Summarize how concentrated a count distribution is."""
    vals = [int(v) for v in values if int(v) >= 0]
    if not vals:
        return ConcentrationSummary(0, 0, 0.0, 0.0, 0, 0.0, 0, 0.0)
    sorted_desc = sorted(vals, reverse=True)
    n = len(sorted_desc)
    total = sum(sorted_desc)
    top_n = max(1, round(n * 0.10))
    n_50 = _items_for_share(sorted_desc, 0.50)
    n_80 = _items_for_share(sorted_desc, 0.80)
    return ConcentrationSummary(
        n_items=n,
        total=total,
        gini=_gini(vals),
        top_10_share_pct=round(100.0 * sum(sorted_desc[:top_n]) / total, 2)
        if total
        else 0.0,
        n_for_50_pct=n_50,
        pct_items_for_50_pct=round(100.0 * n_50 / n, 2) if n else 0.0,
        n_for_80_pct=n_80,
        pct_items_for_80_pct=round(100.0 * n_80 / n, 2) if n else 0.0,
    )


def bootstrap_concentration(
    values: list[int] | tuple[int, ...],
    *,
    n_resamples: int = 300,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapConcentrationSummary:
    """Bootstrap uncertainty for concentration metrics under fixed resampling.

    The resampling unit is the observed item count: song-performance counts for
    repertoire concentration and venue-show counts for venue concentration. The
    interval describes sampling variability of the descriptive statistic under
    item-level resampling; it is exploratory uncertainty, not a causal or
    population-level inference about shows that are absent from the archive.
    """
    vals = np.asarray([int(v) for v in values if int(v) >= 0], dtype=np.int64)
    point = concentration_summary(tuple(int(v) for v in vals.tolist()))
    if vals.size == 0 or n_resamples <= 0:
        empty = BootstrapInterval(
            point=0.0,
            low=0.0,
            high=0.0,
            confidence=confidence,
            n_resamples=max(0, n_resamples),
            seed=seed,
        )
        return BootstrapConcentrationSummary(gini=empty, top_10_share_pct=empty)

    rng = np.random.default_rng(seed)
    gini_samples: list[float] = []
    top_samples: list[float] = []
    n = int(vals.size)
    for _ in range(n_resamples):
        sample = rng.choice(vals, size=n, replace=True)
        summary = concentration_summary(tuple(int(v) for v in sample.tolist()))
        gini_samples.append(summary.gini)
        top_samples.append(summary.top_10_share_pct)

    alpha = (1.0 - confidence) / 2.0

    def _interval(samples: list[float], point_value: float) -> BootstrapInterval:
        ordered = sorted(samples)
        low = _percentile(ordered, alpha)
        high = _percentile(ordered, 1.0 - alpha)
        return BootstrapInterval(
            point=point_value,
            low=min(low, high),
            high=max(low, high),
            confidence=confidence,
            n_resamples=n_resamples,
            seed=seed,
        )

    return BootstrapConcentrationSummary(
        gini=_interval(gini_samples, point.gini),
        top_10_share_pct=_interval(top_samples, point.top_10_share_pct),
    )


def performance_rows_per_show(compendium: Compendium) -> dict[str, int]:
    """Count performance rows per show, including zero-setlist shows."""
    counts: Counter[str] = Counter(p.show_slug for p in compendium.performances)
    return {show.slug: counts.get(show.slug, 0) for show in compendium.shows}


def performance_distribution(compendium: Compendium) -> PerformanceDistribution:
    """Show-level performance-row distribution including empty setlists."""
    values = list(performance_rows_per_show(compendium).values())
    return PerformanceDistribution(
        per_show=summarize_numeric(values),
        n_zero_performance_shows=sum(1 for v in values if v == 0),
    )


def song_performance_counts(
    compendium: Compendium, *, exclude_segments: bool = True
) -> dict[str, int]:
    """Performance counts by song slug, optionally excluding generic segments."""
    counts: Counter[str] = Counter()
    for perf in compendium.performances:
        if exclude_segments and is_segment_marker(perf.song_slug):
            continue
        counts[perf.song_slug] += 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def song_performance_concentration(
    compendium: Compendium, *, exclude_segments: bool = True
) -> ConcentrationSummary:
    """Concentration of performance rows across songs."""
    return concentration_summary(
        list(
            song_performance_counts(
                compendium, exclude_segments=exclude_segments
            ).values()
        )
    )


def venue_show_counts(compendium: Compendium) -> dict[str, int]:
    """Show counts by venue slug."""
    counts: Counter[str] = Counter(show.venue_slug for show in compendium.shows)
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def venue_show_concentration(compendium: Compendium) -> ConcentrationSummary:
    """Concentration of shows across venue slugs."""
    return concentration_summary(list(venue_show_counts(compendium).values()))


def concentration_uncertainty_report(
    compendium: Compendium,
    *,
    n_resamples: int = 300,
    confidence: float = 0.95,
    seed: int = 0,
) -> dict[str, object]:
    """Bootstrap intervals for the two manuscript concentration families."""
    song_counts = tuple(song_performance_counts(compendium).values())
    venue_counts = tuple(venue_show_counts(compendium).values())
    return {
        "method": "fixed-seed item-level bootstrap; descriptive uncertainty only",
        "confidence": confidence,
        "n_resamples": n_resamples,
        "seed": seed,
        "song_performance_concentration": bootstrap_concentration(
            song_counts,
            n_resamples=n_resamples,
            confidence=confidence,
            seed=seed,
        ).to_dict(),
        "venue_show_concentration": bootstrap_concentration(
            venue_counts,
            n_resamples=n_resamples,
            confidence=confidence,
            seed=seed + 1,
        ).to_dict(),
    }
