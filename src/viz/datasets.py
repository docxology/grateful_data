"""Raw CSV/JSON datasets behind rendered figure panels."""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..analysis import (
    bustouts,
    centrality,
    composers,
    cooccurrence,
    distributions,
    eras,
    exploratory,
    first_principles,
    geo,
    lyrics,
    personnel_timeline,
    positions,
    repertoire,
    reviews,
    segues,
    stationary,
    stats,
    timeseries,
    tours,
    transitions,
    venues,
)
from ..cattheory.functors import lineup_functor, setlist_functor
from ..integration.reconcile import Compendium

Cell = str | int | float | bool | None


@dataclass(frozen=True)
class FigureDataset:
    """A deterministic tabular export for one figure."""

    figure: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Cell, ...], ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.figure.endswith(".png"):
            raise ValueError("FigureDataset.figure must be a PNG filename")
        if not self.columns:
            raise ValueError("FigureDataset.columns must be non-empty")
        width = len(self.columns)
        for row in self.rows:
            if len(row) != width:
                raise ValueError(
                    f"row width {len(row)} does not match column width {width}"
                )

    @property
    def stem(self) -> str:
        return self.figure.removesuffix(".png")

    def to_json_payload(self) -> dict[str, Any]:
        return {
            "figure": self.figure,
            "title": self.title,
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "metadata": dict(sorted(self.metadata.items())),
        }

    def write_csv(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(self.columns)
            writer.writerows(self.rows)
        return path

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.to_json_payload(), fh, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def write_pair(self, out_dir: Path) -> tuple[Path, Path]:
        return (
            self.write_csv(out_dir / f"{self.stem}.csv"),
            self.write_json(out_dir / f"{self.stem}.json"),
        )


def _pretty_slug(slug: str) -> str:
    title = slug.replace("_", " ")
    minor = {"the", "of", "in", "on", "a", "and", "to", "my"}
    words = title.split()
    return " ".join(
        word if (idx and word in minor) else word.capitalize()
        for idx, word in enumerate(words)
    )


def _song_title(compendium: Compendium, slug: str) -> str:
    song = compendium.song_by_slug.get(slug)
    return song.title if song else _pretty_slug(slug)


def _dataset(
    figure: str,
    title: str,
    columns: tuple[str, ...],
    rows: Iterable[Iterable[Cell]],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> FigureDataset:
    return FigureDataset(
        figure=figure,
        title=title,
        columns=columns,
        rows=tuple(tuple(row) for row in rows),
        metadata=metadata or {},
    )


def shows_per_year(compendium: Compendium) -> FigureDataset:
    s = stats.compute(compendium, top_n=15)
    perfs = timeseries.performances_per_year(compendium)
    years = sorted(s.shows_per_year)
    return _dataset(
        "shows_per_year.png",
        "Shows and Performances by Year",
        ("year", "n_shows", "n_performance_rows"),
        ((year, s.shows_per_year[year], perfs.get(year, 0)) for year in years),
    )


def top_songs(compendium: Compendium) -> FigureDataset:
    s = stats.compute(compendium, top_n=15)
    return _dataset(
        "top_songs.png",
        "Most-Performed Songs",
        ("rank", "song_slug", "title", "n_performances"),
        (
            (idx, slug, _song_title(compendium, slug), count)
            for idx, (slug, count) in enumerate(s.top_songs, start=1)
        ),
        metadata={
            "exclude_segments": True,
            "segment_marker_counts": [
                {"song_slug": slug, "n_performances": count}
                for slug, count in s.segment_marker_counts
            ],
        },
    )


def cooccurrence_heatmap(compendium: Compendium) -> FigureDataset:
    songs, matrix = cooccurrence.cooccurrence_matrix(compendium, exclude_segments=True)
    diag = np.diag(matrix)
    top_idx = np.argsort(-diag)[:25]
    labels = [songs[i] for i in top_idx]
    rows = []
    for i, src in enumerate(labels):
        for j, dst in enumerate(labels):
            rows.append((src, dst, int(matrix[top_idx[i], top_idx[j]])))
    return _dataset(
        "cooccurrence_heatmap.png",
        "Song Co-occurrence Heatmap",
        ("source_song_slug", "target_song_slug", "n_show_cooccurrences"),
        rows,
        metadata={
            "top_n": len(labels),
            "diagonal_is_song_show_count": True,
            "exclude_segments": True,
        },
    )


def functor_cardinalities(compendium: Compendium) -> FigureDataset:
    f_set = setlist_functor(compendium)
    f_lineup = lineup_functor(compendium)
    dates = sorted(f_set)
    date_text = lambda day: day.isoformat() if hasattr(day, "isoformat") else str(day)
    return _dataset(
        "functor_cardinalities.png",
        "Functor Cardinalities",
        ("date", "show_index", "cumulative_setlist_size", "cumulative_lineup_size"),
        (
            (
                date_text(day),
                idx,
                len(f_set[day]),
                len(f_lineup.get(day, set())),
            )
            for idx, day in enumerate(dates, start=1)
        ),
    )


def transition_matrix(compendium: Compendium) -> FigureDataset:
    s = stats.compute(compendium, top_n=25)
    labels = [slug for slug, _count in s.top_songs]
    model = transitions.fit(compendium, exclude_segments=True)
    rows = []
    for prev in labels:
        if prev not in model.song_slugs:
            continue
        i = model.song_slugs.index(prev)
        for nxt in labels:
            if nxt not in model.song_slugs:
                continue
            j = model.song_slugs.index(nxt)
            rows.append(
                (
                    prev,
                    nxt,
                    int(model.counts[i, j]),
                    round(float(model.transition_matrix[i, j]), 8),
                )
            )
    return _dataset(
        "transition_matrix.png",
        "Markov Transition Matrix",
        ("previous_song_slug", "next_song_slug", "n_transitions", "probability"),
        rows,
        metadata={
            "top_n": len(labels),
            "model": "first_order_markov",
            "exclude_segments": True,
        },
    )


def composer_attribution(compendium: Compendium) -> FigureDataset:
    song_counts = composers.composer_song_counts(compendium)
    perf_counts = composers.composer_performance_counts(compendium)
    top = list(song_counts)[:12]
    return _dataset(
        "composer_attribution.png",
        "Composer Attribution",
        ("composer", "n_songs_written", "n_weighted_performances"),
        ((name, song_counts[name], perf_counts.get(name, 0)) for name in top),
    )


def segue_graph(compendium: Compendium) -> FigureDataset:
    edges = segues.segue_edges(compendium)[:15]
    return _dataset(
        "segue_graph.png",
        "Most Frequent Segues",
        ("rank", "source_song_slug", "target_song_slug", "n_segues"),
        (
            (idx, edge.src, edge.dst, edge.count)
            for idx, edge in enumerate(edges, start=1)
        ),
        metadata={"source": "explicit segue_into markers only"},
    )


def era_density(compendium: Compendium) -> FigureDataset:
    density = eras.year_month_density(compendium)
    return _dataset(
        "era_density.png",
        "Show Density by Month and Year",
        ("year", "month", "n_shows"),
        ((year, month, count) for (year, month), count in density.items()),
    )


def personnel_gantt(compendium: Compendium) -> FigureDataset:
    return _dataset(
        "personnel_gantt.png",
        "Personnel Timeline",
        ("person_slug", "full_name", "start_date", "end_date", "roles"),
        (
            (
                bar.person_slug,
                bar.full_name,
                bar.start.isoformat(),
                bar.end.isoformat() if bar.end else "",
                ";".join(bar.roles),
            )
            for bar in personnel_timeline.bars(compendium)
        ),
    )


def sentiment_by_kind(compendium: Compendium) -> FigureDataset:
    summary = reviews.sentiment_by_kind_summary(compendium)
    return _dataset(
        "sentiment_by_kind.png",
        "Review Sentiment by Source Kind",
        ("kind", "n_reviews", "mean_sentiment", "stdev_sentiment"),
        (
            (
                kind,
                int(values["n"]),
                round(float(values["mean"]), 6),
                round(float(values["stdev"]), 6),
            )
            for kind, values in summary.items()
        ),
    )


def citation_kinds(compendium: Compendium) -> FigureDataset:
    counts = Counter(citation.kind for citation in compendium.citations)
    rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    total = sum(counts.values()) or 1
    return _dataset(
        "citation_kinds.png",
        "Citation Kinds",
        ("kind", "n_citations", "share_pct"),
        ((kind, count, round(100.0 * count / total, 4)) for kind, count in rows),
    )


def recording_sources(compendium: Compendium) -> FigureDataset:
    counts = Counter(recording.source_type for recording in compendium.recordings)
    rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    total = sum(counts.values()) or 1
    return _dataset(
        "recording_sources.png",
        "Recording Source Types",
        ("source_type", "n_recordings", "share_pct"),
        ((kind, count, round(100.0 * count / total, 4)) for kind, count in rows),
    )


def shows_by_era(compendium: Compendium) -> FigureDataset:
    counts = eras.shows_by_era(compendium)
    return _dataset(
        "shows_by_era.png",
        "Shows by Era",
        ("era", "n_shows"),
        counts.items(),
    )


def lyric_themes(compendium: Compendium) -> FigureDataset:
    freq = lyrics.theme_frequencies(compendium)
    return _dataset(
        "lyric_themes.png",
        "Lyric Pointer Themes",
        ("theme", "n_pointer_tags"),
        list(freq.items())[:20],
        metadata={"source": "lyric pointer metadata only; no lyric text bundled"},
    )


def lineup_diversity(compendium: Compendium) -> FigureDataset:
    diversity = personnel_timeline.lineup_diversity(compendium)
    return _dataset(
        "lineup_diversity.png",
        "Active Lineup Size",
        ("date", "active_member_count"),
        diversity.items(),
    )


def geo_scatter(compendium: Compendium) -> FigureDataset:
    geo_map = geo.load_geo()
    show_counts = Counter(show.venue_slug for show in compendium.shows)
    slugs = sorted(set(show_counts) & set(geo_map))
    return _dataset(
        "geo_scatter.png",
        "Venue Geography",
        ("venue_slug", "latitude", "longitude", "region", "n_shows"),
        (
            (
                slug,
                float(geo_map[slug]["lat"]),
                float(geo_map[slug]["lon"]),
                str(geo_map[slug]["region"]),
                show_counts[slug],
            )
            for slug in slugs
        ),
        metadata={"geocoded_venues": len(slugs)},
    )


def set_positions(compendium: Compendium) -> FigureDataset:
    dist = positions.position_distribution(compendium)
    return _dataset(
        "set_positions.png",
        "Set-Position Distribution",
        ("position", "n_performance_rows"),
        dist.items(),
    )


def performance_distribution(compendium: Compendium) -> FigureDataset:
    counts = distributions.performance_rows_per_show(compendium)
    return _dataset(
        "performance_distribution.png",
        "Performance Rows per Show",
        ("show_slug", "n_performance_rows"),
        counts.items(),
        metadata=distributions.performance_distribution(compendium).to_dict(),
    )


def _concentration_rows(
    compendium: Compendium, counts: Mapping[str, int], *, song_labels: bool
) -> tuple[tuple[Cell, ...], ...]:
    total = sum(counts.values()) or 1
    running = 0
    rows = []
    for rank, (slug, count) in enumerate(counts.items(), start=1):
        running += count
        title = _song_title(compendium, slug) if song_labels else _pretty_slug(slug)
        rows.append((rank, slug, title, count, round(100.0 * running / total, 6)))
    return tuple(rows)


def repertoire_concentration(compendium: Compendium) -> FigureDataset:
    counts = distributions.song_performance_counts(compendium)
    return _dataset(
        "repertoire_concentration.png",
        "Repertoire Concentration",
        ("rank", "song_slug", "title", "n_performances", "cumulative_share_pct"),
        _concentration_rows(compendium, counts, song_labels=True),
        metadata=distributions.song_performance_concentration(compendium).to_dict(),
    )


def venue_concentration(compendium: Compendium) -> FigureDataset:
    counts = distributions.venue_show_counts(compendium)
    return _dataset(
        "venue_concentration.png",
        "Venue Concentration",
        ("rank", "venue_slug", "label", "n_shows", "cumulative_share_pct"),
        _concentration_rows(compendium, counts, song_labels=False),
        metadata=distributions.venue_show_concentration(compendium).to_dict(),
    )


def stationary_top20(compendium: Compendium) -> FigureDataset:
    model = transitions.fit(compendium, exclude_segments=True)
    dist = stationary.compute(model)
    rows = sorted(dist.items(), key=lambda item: (-item[1], item[0]))[:20]
    return _dataset(
        "stationary_top20.png",
        "Markov Stationary Distribution",
        ("rank", "song_slug", "title", "stationary_probability"),
        (
            (idx, slug, _song_title(compendium, slug), round(float(value), 8))
            for idx, (slug, value) in enumerate(rows, start=1)
        ),
        metadata={"model": "first_order_markov_stationary", "exclude_segments": True},
    )


def centrality_top20(compendium: Compendium) -> FigureDataset:
    songs, matrix = cooccurrence.cooccurrence_matrix(compendium, exclude_segments=True)
    scores = centrality.eigenvector_centrality(
        songs, cooccurrence.jaccard_matrix(matrix)
    )
    rows = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:20]
    return _dataset(
        "centrality_top20.png",
        "Association Centrality",
        ("rank", "song_slug", "title", "eigenvector_centrality"),
        (
            (idx, slug, _song_title(compendium, slug), round(float(value), 8))
            for idx, (slug, value) in enumerate(rows, start=1)
        ),
        metadata={"adjacency": "Jaccard co-occurrence", "exclude_segments": True},
    )


def releases_timeline(compendium: Compendium) -> FigureDataset:
    return _dataset(
        "releases_timeline.png",
        "Release Timeline",
        ("release_slug", "title", "release_date", "kind", "n_track_show_slugs"),
        (
            (
                release.slug,
                release.title,
                release.release_date.isoformat(),
                release.kind,
                len(release.track_show_slugs),
            )
            for release in compendium.releases
        ),
    )


def context_timeline(compendium: Compendium) -> FigureDataset:
    s = stats.compute(compendium, top_n=15)
    markers = {
        1965: "Warlocks/Acid Tests",
        1969: "Live/Dead",
        1970: "Workingman's/American Beauty",
        1974: "Wall of Sound",
        1984: "Taper section",
        1987: "Touch of Grey",
        1995: "Final show/Garcia",
    }
    return _dataset(
        "context_timeline.png",
        "Historical Context Timeline",
        ("year", "n_shows", "context_marker"),
        (
            (year, s.shows_per_year[year], markers.get(year, ""))
            for year in sorted(s.shows_per_year)
        ),
        metadata={"context_markers_are_interpretive_overlays": True},
    )


def tours_top(compendium: Compendium) -> FigureDataset:
    rows = list(tours.shows_per_tour(compendium).items())[:15]
    return _dataset(
        "tours_top.png",
        "Top Tours",
        ("tour", "n_shows"),
        rows,
    )


def bustouts_dataset(compendium: Compendium) -> FigureDataset:
    rows = bustouts.biggest_bustouts(compendium, top_n=15)
    return _dataset(
        "bustouts.png",
        "Recurrence Gaps",
        ("rank", "song_slug", "title", "n_show_performances", "max_gap_shows"),
        (
            (
                idx,
                row.song_slug,
                _song_title(compendium, row.song_slug),
                row.n_performances,
                row.max_gap_shows,
            )
            for idx, row in enumerate(rows, start=1)
        ),
    )


def song_lifespans(compendium: Compendium) -> FigureDataset:
    from ..analysis import repertoire

    rows = repertoire.song_lifespans(compendium, top_n=25)
    return _dataset(
        "song_lifespans.png",
        "Song Lifespans",
        (
            "song_slug",
            "title",
            "first_year",
            "last_year",
            "span_years",
            "n_performances",
            "debut_era",
        ),
        (
            (
                row.song_slug,
                _song_title(compendium, row.song_slug),
                row.first_year,
                row.last_year,
                row.span_years,
                row.n_performances,
                row.debut_era,
            )
            for row in rows
        ),
    )


def repertoire_embedding(compendium: Compendium) -> FigureDataset:
    emb = exploratory.repertoire_embedding(compendium, top_n=80, n_clusters=5)
    return _dataset(
        "repertoire_embedding.png",
        "Exploratory Repertoire Embedding",
        (
            "song_slug",
            "title",
            "svd_component_1",
            "svd_component_2",
            "cluster",
            "n_performances",
            "dominant_era",
            "dominant_era_share",
        ),
        (
            (
                song.song_slug,
                song.title,
                song.x,
                song.y,
                song.cluster,
                song.n_performances,
                song.dominant_era,
                song.dominant_era_share,
            )
            for song in emb.songs
        ),
        metadata={
            "method_note": emb.method_note,
            "component_1_variance_share": emb.component_variance_share[0],
            "component_2_variance_share": emb.component_variance_share[1],
            "n_clusters": len(emb.clusters),
        },
    )


def concentration_uncertainty(compendium: Compendium) -> FigureDataset:
    report = distributions.concentration_uncertainty_report(compendium)
    rows = []
    for family, key in (
        ("song_performance_concentration", "song_performance_concentration"),
        ("venue_show_concentration", "venue_show_concentration"),
    ):
        payload = report[key]
        for metric in ("gini", "top_10_share_pct"):
            interval = payload[metric]
            rows.append(
                (
                    family,
                    metric,
                    interval["point"],
                    interval["low"],
                    interval["high"],
                    interval["confidence"],
                    interval["n_resamples"],
                    interval["seed"],
                )
            )
    return _dataset(
        "concentration_uncertainty.png",
        "Concentration Uncertainty",
        (
            "family",
            "metric",
            "point",
            "ci_low",
            "ci_high",
            "confidence",
            "n_resamples",
            "seed",
        ),
        rows,
        metadata={"method": report["method"]},
    )


def transition_sensitivity(compendium: Compendium) -> FigureDataset:
    report = transitions.transition_sensitivity_report(compendium, include_era_models=False)
    rows = []
    for row in report["segment_marker_policies"]:
        rows.append(
            (
                bool(row["exclude_segments"]),
                int(row["min_predecessor_support"]),
                int(row["n_songs"]),
                int(row["n_observed_transitions"]),
                int(row["n_nonzero_edges"]),
                int(row["n_supported_predecessors"]),
                int(row["n_supported_edges"]),
                round(
                    100.0
                    * int(row["n_supported_edges"])
                    / max(1, int(row["n_nonzero_edges"])),
                    6,
                ),
                round(
                    100.0
                    * int(row["n_supported_predecessors"])
                    / max(1, int(row["n_songs"])),
                    6,
                ),
            )
        )
    return _dataset(
        "transition_sensitivity.png",
        "Transition Sensitivity",
        (
            "exclude_segments",
            "min_predecessor_support",
            "n_songs",
            "n_observed_transitions",
            "n_nonzero_edges",
            "n_supported_predecessors",
            "n_supported_edges",
            "supported_edge_share_pct",
            "supported_predecessor_share_pct",
        ),
        rows,
        metadata={"method": report["method"]},
    )


def repertoire_topn_sensitivity(compendium: Compendium) -> FigureDataset:
    report = repertoire.repertoire_topn_sensitivity(compendium)
    rows = []
    for row in report["rows"]:
        coverages = [
            float(era_row["era_performance_share_pct"])
            for era_row in row["era_coverage"]
        ]
        rows.append(
            (
                int(row["top_n"]),
                int(row["n_available"]),
                int(row["selected_performances"]),
                float(row["performance_share_pct"]),
                float(row["gini_within_cut"]),
                float(row["top_10_share_pct_within_cut"]),
                round(min(coverages), 6) if coverages else 0.0,
                round(sum(coverages) / len(coverages), 6) if coverages else 0.0,
                round(max(coverages), 6) if coverages else 0.0,
            )
        )
    return _dataset(
        "repertoire_topn_sensitivity.png",
        "Repertoire Top-N Sensitivity",
        (
            "top_n",
            "n_available",
            "selected_performances",
            "performance_share_pct",
            "gini_within_cut",
            "top_10_share_pct_within_cut",
            "min_era_share_pct",
            "mean_era_share_pct",
            "max_era_share_pct",
        ),
        rows,
        metadata={
            "method": report["method"],
            "exclude_segments": bool(report["exclude_segments"]),
            "total_non_segment_performances": int(
                report["total_non_segment_performances"]
            ),
        },
    )


def venue_identity_review(compendium: Compendium) -> FigureDataset:
    report = venues.venue_identity_review(compendium)
    summary = report["summary"]
    rows = [
        ("venue_slugs", int(summary["n_venue_slugs"])),
        ("alias_slugs_present", int(summary["n_alias_slugs_present"])),
        ("venues_after_canonicalization", int(summary["n_venues_after_canonicalization"])),
        ("venues_collapsed", int(summary["n_venues_collapsed"])),
        (
            "ambiguous_same_date_collisions",
            int(summary["n_ambiguous_same_date_collisions"]),
        ),
    ]
    return _dataset(
        "venue_identity_review.png",
        "Venue Identity Review",
        ("metric", "value"),
        rows,
        metadata={
            "method": report["method"],
            "policy": report["policy"],
            "mean_collision_setlist_jaccard": summary[
                "mean_collision_setlist_jaccard"
            ],
            "n_alias_decisions": len(report["alias_decisions"]),
            "n_negative_controls": len(report["negative_controls"]),
        },
    )


def era_repertoire_heatmap(compendium: Compendium) -> FigureDataset:
    matrix = exploratory.era_song_matrix(compendium, top_n=20)
    rows = []
    for era_idx, era in enumerate(matrix.eras):
        for song_idx, slug in enumerate(matrix.song_slugs):
            rows.append(
                (
                    era,
                    slug,
                    _song_title(compendium, slug),
                    int(matrix.counts[era_idx, song_idx]),
                    round(float(matrix.normalized[era_idx, song_idx] * 100.0), 8),
                )
            )
    return _dataset(
        "era_repertoire_heatmap.png",
        "Era Repertoire Heatmap",
        ("era", "song_slug", "title", "n_performances", "era_share_pct"),
        rows,
        metadata={"normalization": "within-era performance-row share"},
    )


def claim_evidence_matrix(compendium: Compendium) -> FigureDataset:
    matrix, claim_classes, artifact_families = first_principles.claim_evidence_matrix(
        compendium
    )
    rows = []
    for row_idx, claim_class in enumerate(claim_classes):
        for col_idx, family in enumerate(artifact_families):
            rows.append((claim_class, family, int(matrix[row_idx][col_idx])))
    summary = first_principles.review_summary(compendium)
    return _dataset(
        "claim_evidence_matrix.png",
        "First-Principles Claim Evidence Map",
        ("claim_class", "artifact_family", "n_claim_families"),
        rows,
        metadata={
            "method": "claim-ledger governance matrix; counts are claim families, not corpus observations",
            "n_claim_areas": summary["n_claim_areas"],
            "n_hard_constraints": summary["n_hard_constraints"],
            "n_assumptions": summary["n_assumptions"],
            "n_validation_artifacts": summary["n_validation_artifacts"],
        },
    )


def export_figure_datasets(
    compendium: Compendium, specs: Iterable[Any], out_dir: Path
) -> Path:
    """Write CSV/JSON exports and an index for all specs with datasets."""
    out_dir.mkdir(parents=True, exist_ok=True)
    index_rows = []
    for spec in specs:
        dataset_fn = getattr(spec, "dataset", None)
        if dataset_fn is None:
            continue
        dataset = dataset_fn(compendium)
        csv_path, json_path = dataset.write_pair(out_dir)
        index_rows.append(
            {
                "figure": dataset.figure,
                "title": dataset.title,
                "display_title": getattr(spec, "display_title", dataset.title),
                "alt_text": getattr(spec, "alt_text", ""),
                "caption_hint": getattr(spec, "caption_hint", ""),
                "data_source": getattr(spec, "data_source", ""),
                "statistic": getattr(spec, "statistic", ""),
                "exclusion_rule": getattr(spec, "exclusion_rule", ""),
                "claim_class": getattr(spec, "claim_class", ""),
                "csv": csv_path.name,
                "json": json_path.name,
                "n_rows": len(dataset.rows),
                "columns": list(dataset.columns),
                "metadata": dict(sorted(dataset.metadata.items())),
            }
        )
    payload = {
        "n_datasets": len(index_rows),
        "datasets": sorted(index_rows, key=lambda row: row["figure"]),
    }
    index_path = out_dir / "index.json"
    with index_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return index_path
