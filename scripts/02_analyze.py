#!/usr/bin/env python3
"""Run descriptive + transition analyses on the seed compendium."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis import (  # noqa: E402
    cooccurrence,
    distributions,
    exploratory,
    first_principles,
    network,
    repertoire,
    reviews,
    segues,
    stats,
    timeseries,
    transitions,
    venues as venues_analysis,
)
from src.seed import load_seed_compendium  # noqa: E402
from src.tier import resolve_seed_dir  # noqa: E402


def main() -> None:
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp = load_seed_compendium()
    tier = resolve_seed_dir().name

    s = stats.compute(comp, top_n=15)
    songs, m = cooccurrence.cooccurrence_matrix(comp)
    tm = transitions.fit(comp)
    py = timeseries.performances_per_year(comp)
    deg = network.venue_degrees(comp)

    top_songs_list = [{"slug": slug, "count": count} for slug, count in s.top_songs]
    top_song = top_songs_list[0]["slug"] if top_songs_list else ""
    top_song_count = top_songs_list[0]["count"] if top_songs_list else 0

    coverage = repertoire.catalog_coverage(comp)
    turnover = repertoire.repertoire_turnover(comp)
    venue_dup = venues_analysis.venue_duplication_report(comp)
    perf_dist = distributions.performance_distribution(comp)
    song_conc = distributions.song_performance_concentration(comp)
    venue_conc = distributions.venue_show_concentration(comp)
    uncertainty = distributions.concentration_uncertainty_report(comp)
    exploratory_repertoire = exploratory.exploratory_repertoire_report(comp)
    segue_edges = segues.segue_edges(comp)
    segue_out = segues.segue_out_degree(comp)
    sig_summary = transitions.transition_significance_summary(
        comp, min_support=20, n_permutations=200, fdr_q=0.05, seed=0
    )
    transition_sensitivity = transitions.transition_sensitivity_report(comp)
    repertoire_sensitivity = repertoire.repertoire_topn_sensitivity(comp)
    venue_identity = venues_analysis.venue_identity_review(comp)
    sig_transitions = sig_summary["significant"]

    report = {
        "tier": tier,
        "top_line": {
            "n_shows": s.n_shows,
            "n_songs": s.n_songs,
            "n_people": s.n_people,
            "n_venues": s.n_venues,
            "n_performances": s.n_performances,
            "n_recordings": s.n_recordings,
            "n_releases": s.n_releases,
            "n_citations": s.n_citations,
        },
        "shows_per_year": s.shows_per_year,
        "performances_per_year": py,
        "top_songs": top_songs_list,
        "top_songs_top3": top_songs_list[:3],
        "top_song": top_song,
        "top_song_count": top_song_count,
        "top_venues_by_shows": [
            {"slug": d.venue_slug, "n_shows": d.n_shows, "n_songs": d.n_distinct_songs}
            for d in sorted(deg, key=lambda d: d.n_shows, reverse=True)[:10]
        ],
        "cooccurrence_dim": len(songs),
        "transitions_dim": len(tm.song_slugs),
        "date_poset_objects": len({s.date for s in comp.shows}),
        "segment_marker_counts": [
            {"slug": slug, "count": count} for slug, count in s.segment_marker_counts
        ],
        "catalog_coverage": {
            "n_catalog": coverage.n_catalog,
            "n_performed_in_catalog": coverage.n_performed_in_catalog,
            "n_never_performed": coverage.n_never_performed,
            "coverage_pct": coverage.coverage_pct,
            "n_performed_not_in_catalog": coverage.n_performed_not_in_catalog,
            "n_segment_markers_performed": coverage.n_segment_markers_performed,
        },
        "repertoire_turnover": [
            {
                "era_a": t.era_a,
                "era_b": t.era_b,
                "jaccard": t.jaccard,
                "turnover": t.turnover,
                "shared": t.shared,
            }
            for t in turnover
        ],
        "venue_duplication": {
            "n_venue_slugs": venue_dup.n_venue_slugs,
            "n_alias_slugs_present": venue_dup.n_alias_slugs_present,
            "n_venues_after_canonicalization": venue_dup.n_venues_after_canonicalization,
            "n_venues_collapsed": venue_dup.n_venues_collapsed,
            "n_ambiguous_same_date_collisions": venue_dup.n_ambiguous_same_date_collisions,
            "mean_collision_setlist_jaccard": venue_dup.mean_collision_setlist_jaccard,
        },
        "venue_identity_review": venue_identity,
        "statistical_shape": {
            "performance_rows_per_show": perf_dist.to_dict(),
            "song_performance_concentration": song_conc.to_dict(),
            "venue_show_concentration": venue_conc.to_dict(),
            "concentration_uncertainty": uncertainty,
            "repertoire_topn_sensitivity": repertoire_sensitivity,
        },
        "exploratory_repertoire": exploratory_repertoire,
        "first_principles_review": first_principles.review_summary(comp),
        "significant_transitions_n": sig_summary["n_fdr_significant"],
        "transition_significance": {
            "n_candidates": sig_summary["n_candidates"],
            "n_uncorrected": sig_summary["n_uncorrected"],
            "n_fdr_significant": sig_summary["n_fdr_significant"],
            "fdr_q": sig_summary["fdr_q"],
            "n_permutations": sig_summary["n_permutations"],
        },
        "transition_sensitivity": transition_sensitivity,
        "significant_transitions_top": [
            {"prev": prev, "next": nxt, "count": int(obs)}
            for prev, nxt, obs, _thr in sig_transitions[:15]
        ],
        "segue_summary": {
            "n_distinct_edges": len(segue_edges),
            "top_segue_src": segue_edges[0].src if segue_edges else "",
            "top_segue_dst": segue_edges[0].dst if segue_edges else "",
            "top_segue_count": segue_edges[0].count if segue_edges else 0,
            "top_out_degree_song": next(iter(segue_out), ""),
            "top_out_degree_count": next(iter(segue_out.values()), 0),
        },
        "sentiment_by_kind": reviews.sentiment_by_kind_summary(comp),
    }

    out = out_dir / "analysis_report.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(out)


if __name__ == "__main__":
    main()
