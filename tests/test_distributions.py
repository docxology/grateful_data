"""Distribution and concentration summaries."""

from __future__ import annotations

from src.analysis import distributions


def test_numeric_summary_reports_robust_percentiles():
    summary = distributions.summarize_numeric([0, 1, 2, 3, 100])
    assert summary.n == 5
    assert summary.minimum == 0
    assert summary.median == 2
    assert summary.p90 == 61.2
    assert summary.maximum == 100
    assert summary.iqr == 2


def test_concentration_summary_identifies_pareto_skew():
    summary = distributions.concentration_summary([50, 25, 15, 10])
    assert summary.total == 100
    assert summary.n_for_50_pct == 1
    assert summary.n_for_80_pct == 3
    assert summary.top_10_share_pct == 50
    assert summary.gini > 0


def test_performance_distribution_includes_empty_shows(compendium):
    report = distributions.performance_distribution(compendium)
    assert report.per_show.n == len(compendium.shows)
    assert report.per_show.maximum >= report.per_show.median
    assert report.n_zero_performance_shows >= 0


def test_song_and_venue_concentration_use_real_compendium(compendium):
    song_summary = distributions.song_performance_concentration(compendium)
    venue_summary = distributions.venue_show_concentration(compendium)
    assert song_summary.total > 0
    assert venue_summary.total == len(compendium.shows)
    assert song_summary.n_for_80_pct >= song_summary.n_for_50_pct
    assert venue_summary.n_for_80_pct >= venue_summary.n_for_50_pct


def test_bootstrap_concentration_is_fixed_seed_and_ordered():
    first = distributions.bootstrap_concentration(
        [50, 25, 15, 10], n_resamples=40, seed=7
    )
    second = distributions.bootstrap_concentration(
        [50, 25, 15, 10], n_resamples=40, seed=7
    )
    assert first.to_dict() == second.to_dict()
    assert first.gini.low <= first.gini.point <= first.gini.high
    assert (
        first.top_10_share_pct.low
        <= first.top_10_share_pct.point
        <= first.top_10_share_pct.high
    )


def test_concentration_uncertainty_report_names_families(compendium):
    report = distributions.concentration_uncertainty_report(
        compendium, n_resamples=20, seed=3
    )
    assert report["method"].startswith("fixed-seed")
    assert "song_performance_concentration" in report
    assert "venue_show_concentration" in report
