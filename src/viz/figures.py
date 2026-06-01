"""Single source of truth for figure specs, rendering, and expected filenames."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from ..analysis import stats
from ..integration.reconcile import Compendium
from . import datasets, panels, style

DrawFn = Callable[[Axes, Compendium], bool | None]
DatasetFn = Callable[[Compendium], datasets.FigureDataset]
FigureGroup = Literal["core", "extended", "more"]


@dataclass(frozen=True)
class FigureSpec:
    filename: str
    figsize: tuple[float, float]
    draw: DrawFn
    group: FigureGroup
    dashboard: bool = True
    apply_style: bool = True
    title: str = ""
    alt_text: str = ""
    caption_hint: str = ""
    data_source: str = "Registered compendium/report data for the selected tier"
    statistic: str = "Figure-specific statistic documented by the caption and exported dataset columns"
    exclusion_rule: str = "Loaded-tier scope; figure-specific exclusions are documented in the caption"
    claim_class: str = "descriptive"
    dataset: DatasetFn | None = None
    dataset_reason: str = ""

    @property
    def display_title(self) -> str:
        return self.title or self.filename.removesuffix(".png").replace("_", " ")


def _draw_cooccurrence(ax: Axes, comp: Compendium) -> None:
    panels.draw_cooccurrence_heatmap(ax, comp)


def _draw_transition(ax: Axes, comp: Compendium) -> None:
    s = stats.compute(comp, top_n=25)
    labels = [slug for slug, _count in s.top_songs]
    panels.draw_transition_matrix(ax, comp, labels)


def _draw_shows_per_year(ax: Axes, comp: Compendium) -> None:
    panels.draw_shows_and_performances_per_year(ax, comp)


FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        "shows_per_year.png",
        (7.5, 4),
        _draw_shows_per_year,
        "core",
        title="Shows and Performances by Year",
        alt_text="Yearly bars count shows while an overlaid line counts performance rows, making late-1970s and late-1980s touring intensity visible.",
        caption_hint="Temporal activity in the selected compendium tier.",
        data_source="Bundled show and performance tables.",
        statistic="Annual show count and annual performance-row count.",
        exclusion_rule="No shows are dropped; empty-setlist shows contribute to show counts but not performance-row totals.",
        dataset=datasets.shows_per_year,
    ),
    FigureSpec(
        "top_songs.png",
        (7.5, 4),
        panels.draw_top_songs,
        "core",
        title="Most-Performed Songs",
        alt_text="Ranked horizontal bars show the top non-segment songs by performance count; the longest bar is Playing in the Band.",
        caption_hint="Top repertoire counts computed from performance rows.",
        data_source="Bundled performance rows joined to song metadata.",
        statistic="Top-song performance counts.",
        exclusion_rule="Generic segment markers are excluded and surfaced separately.",
        dataset=datasets.top_songs,
    ),
    FigureSpec(
        "cooccurrence_heatmap.png",
        (8, 7),
        _draw_cooccurrence,
        "core",
        title="Song Co-occurrence Heatmap",
        alt_text="Square heatmap compares show-level co-occurrence among top non-segment songs; brighter cells mark song pairs that share more shows.",
        caption_hint="Cell values count shows in which both songs appear.",
        data_source="Bundled show/performance rows.",
        statistic="Show-level pairwise co-occurrence counts.",
        exclusion_rule="Generic segment markers are excluded.",
        dataset=datasets.cooccurrence_heatmap,
    ),
    FigureSpec(
        "functor_cardinalities.png",
        (7.5, 4),
        panels.draw_functor_cardinalities,
        "core",
        title="Functor Cardinalities",
        alt_text="Two cumulative lines compare setlist growth and active lineup growth over chronological show index.",
        caption_hint="Machine-checked monotone cumulative functor sizes.",
        data_source="Bundled ordered performances and curated personnel intervals.",
        statistic="Cumulative setlist and lineup cardinalities.",
        exclusion_rule="Cumulative functor construction includes all loaded performances and personnel intervals.",
        claim_class="validation",
        dataset=datasets.functor_cardinalities,
    ),
    FigureSpec(
        "transition_matrix.png",
        (8, 7),
        _draw_transition,
        "core",
        title="Markov Transition Matrix",
        alt_text="Probability heatmap for first-order song successors among top non-segment songs, with the China Cat Sunflower to I Know You Rider cell brightest.",
        caption_hint="Rows are observed within-show successors normalized to probabilities.",
        data_source="Ordered bundled performance rows.",
        statistic="First-order within-show transition probability.",
        exclusion_rule="Generic segment markers are excluded; sensitivity is reported separately.",
        claim_class="exploratory",
        dataset=datasets.transition_matrix,
    ),
    FigureSpec(
        "composer_attribution.png",
        (8, 4.5),
        panels.draw_composer_attribution,
        "extended",
        title="Composer Attribution",
        alt_text="Grouped bars comparing songs written with performance-weighted composer counts.",
        caption_hint="Composer credit counts versus performance-weighted attribution.",
        data_source="Bundled song composer fields joined to performance rows.",
        statistic="Songs written versus performance-weighted composer attribution.",
        exclusion_rule="Songs without composer metadata do not contribute composer-credit rows.",
        dataset=datasets.composer_attribution,
    ),
    FigureSpec(
        "segue_graph.png",
        (9, 5.5),
        panels.draw_segue_graph,
        "extended",
        apply_style=False,
        title="Most Frequent Segues",
        alt_text="Ranked horizontal bars show explicit source-marked segue edges; Drums to Space and China Cat Sunflower to I Know You Rider dominate.",
        caption_hint="Explicit source-marked segue edges, not inferred adjacency.",
        data_source="Ordered performance rows with source-marked segue_into flags.",
        statistic="Explicit segue edge counts.",
        exclusion_rule="Uses only source-marked segue_into relations; adjacency is not inferred.",
        dataset=datasets.segue_graph,
    ),
    FigureSpec(
        "era_density.png",
        (8, 4),
        panels.draw_era_density,
        "extended",
        title="Show Density by Month and Year",
        alt_text="Year-by-month heatmap of show density.",
        caption_hint="Calendar density across the selected compendium tier.",
        data_source="Bundled show dates.",
        statistic="Show counts by calendar year and month.",
        exclusion_rule="No shows are dropped; empty-setlist shows still count as shows.",
        dataset=datasets.era_density,
    ),
    FigureSpec(
        "personnel_gantt.png",
        (9, 6),
        panels.draw_personnel_gantt,
        "extended",
        title="Personnel Timeline",
        alt_text="Gantt chart of band-member active intervals.",
        caption_hint="Curated personnel intervals used by lineup analyses.",
        data_source="Curated personnel interval table.",
        statistic="Membership/role intervals displayed as horizontal date ranges.",
        exclusion_rule="Only explicit interval metadata is plotted; inferred guest appearances are outside scope.",
        dataset=datasets.personnel_gantt,
    ),
    FigureSpec(
        "sentiment_by_kind.png",
        (7, 4),
        panels.draw_sentiment_by_kind,
        "extended",
        title="Review Sentiment by Source Kind",
        alt_text="Bar chart of mean review sentiment grouped by source kind.",
        caption_hint="Curated review-pointer sentiment aggregates.",
        data_source="Bundled review-pointer table.",
        statistic="Mean sentiment by source kind with support and dispersion.",
        exclusion_rule="Reviews without pointer/source metadata are not fabricated.",
        dataset=datasets.sentiment_by_kind,
    ),
    FigureSpec(
        "citation_kinds.png",
        (7, 4),
        panels.draw_citation_kinds_pie,
        "extended",
        apply_style=False,
        title="Citation Kinds",
        alt_text="Ranked bar chart of bibliography citation kinds.",
        caption_hint="Citation kind mix after bibliography and references merge.",
        data_source="Bibliography markdown, BibTeX, and archival citation rows.",
        statistic="Citation-kind counts and share of total.",
        exclusion_rule="Citation rows are metadata pointers; no source text is bundled.",
        dataset=datasets.citation_kinds,
    ),
    FigureSpec(
        "recording_sources.png",
        (7, 4),
        panels.draw_recording_sources_pie,
        "extended",
        apply_style=False,
        title="Recording Source Types",
        alt_text="Ranked bar chart of recording source-type counts.",
        caption_hint="Recording metadata source labels in the compendium.",
        data_source="Bundled recording metadata.",
        statistic="Recording counts and shares by source-type label.",
        exclusion_rule="Missing source-type labels remain UNKNOWN; source type is not inferred from audio.",
        dataset=datasets.recording_sources,
    ),
    FigureSpec(
        "shows_by_era.png",
        (8, 4),
        panels.draw_shows_by_era,
        "extended",
        title="Shows by Era",
        alt_text="Bar chart of show counts by era label.",
        caption_hint="Era labels used for density and flow summaries.",
        data_source="Bundled show dates and deterministic era windows.",
        statistic="Show counts by era bucket.",
        exclusion_rule="Era labels are analytical bins rather than source claims.",
        dataset=datasets.shows_by_era,
    ),
    FigureSpec(
        "lyric_themes.png",
        (7, 5),
        panels.draw_lyric_themes,
        "extended",
        title="Lyric Pointer Themes",
        alt_text="Horizontal bar chart of theme tags attached to lyric pointers.",
        caption_hint="Theme frequencies from pointer metadata only.",
        data_source="CMU, dead.net, and curated lyric pointer metadata.",
        statistic="Theme-tag frequencies.",
        exclusion_rule="Lyric text is not bundled, parsed, quoted, or derived.",
        dataset=datasets.lyric_themes,
    ),
    FigureSpec(
        "lineup_diversity.png",
        (8, 4),
        panels.draw_lineup_diversity,
        "extended",
        title="Active Lineup Size",
        alt_text="Line chart of active lineup size over show dates.",
        caption_hint="Instantaneous active roster size, not cumulative membership.",
        data_source="Bundled show dates and curated personnel intervals.",
        statistic="Active-member count over distinct show dates.",
        exclusion_rule="Counts use interval coverage on each date and are not cumulative roster totals.",
        dataset=datasets.lineup_diversity,
    ),
    FigureSpec(
        "geo_scatter.png",
        (9, 6),
        panels.draw_geo_scatter,
        "more",
        title="Venue Geography",
        alt_text="Geographic scatterplot of venues sized by show count and colored by region.",
        caption_hint="Venue geo sidecar coverage and regional distribution.",
        data_source="Bundled venue table plus geo sidecar.",
        statistic="Geocoded venue points sized by show count.",
        exclusion_rule="Only venues with geocoded sidecar rows are plotted.",
        dataset=datasets.geo_scatter,
    ),
    FigureSpec(
        "set_positions.png",
        (7, 4),
        panels.draw_set_positions,
        "more",
        title="Set-Position Distribution",
        alt_text="Bar chart of performance counts by position within set.",
        caption_hint="Distribution of ordered performance positions.",
        data_source="Bundled ordered performance rows.",
        statistic="Performance-row counts by within-set position index.",
        exclusion_rule="All loaded performance rows with positions are counted, including segment markers.",
        dataset=datasets.set_positions,
    ),
    FigureSpec(
        "performance_distribution.png",
        (8, 4.5),
        panels.draw_performance_distribution,
        "more",
        title="Performance Rows per Show",
        alt_text="Histogram of non-empty setlist lengths with median and p90 reference lines plus a callout for empty-setlist shows.",
        caption_hint="Show-level setlist-size distribution, including empty setlists.",
        data_source="Bundled show/performance tables.",
        statistic="Performance rows per show with median, p90, and empty-setlist count.",
        exclusion_rule="Histogram bins show non-empty setlists; empty setlists are counted in the callout and dataset.",
        dataset=datasets.performance_distribution,
    ),
    FigureSpec(
        "repertoire_concentration.png",
        (8, 4.5),
        panels.draw_repertoire_concentration,
        "more",
        title="Repertoire Concentration",
        alt_text="Cumulative curve rises quickly, showing that a small share of ranked non-segment songs accounts for most performance rows.",
        caption_hint="Pareto-style concentration of song-performance rows, excluding generic segments.",
        data_source="Bundled performance rows joined to song metadata.",
        statistic="Ranked cumulative share, Gini, top-decile share, and 50/80 percent coverage thresholds.",
        exclusion_rule="Generic segment markers are excluded.",
        dataset=datasets.repertoire_concentration,
    ),
    FigureSpec(
        "venue_concentration.png",
        (8, 4.5),
        panels.draw_venue_concentration,
        "more",
        title="Venue Concentration",
        alt_text="Cumulative curve shows how ranked venue slugs account for show rows, with reference guides at 50 and 80 percent.",
        caption_hint="Pareto-style concentration of show rows across venue slugs.",
        data_source="Bundled show and venue tables.",
        statistic="Ranked cumulative show share, Gini, top-decile share, and 50/80 percent coverage thresholds.",
        exclusion_rule="Uses conservative source-derived venue slugs; venue identity review is report-only.",
        dataset=datasets.venue_concentration,
    ),
    FigureSpec(
        "stationary_top20.png",
        (8, 5),
        panels.draw_stationary_top,
        "more",
        title="Markov Stationary Distribution",
        alt_text="Horizontal bars rank non-segment songs by stationary probability under the first-order transition model.",
        caption_hint="Long-run mass under the first-order transition model.",
        data_source="Ordered bundled performance rows.",
        statistic="Stationary probability under a first-order Markov model.",
        exclusion_rule="Generic segment markers are excluded.",
        claim_class="exploratory",
        dataset=datasets.stationary_top20,
    ),
    FigureSpec(
        "centrality_top20.png",
        (8, 5),
        panels.draw_centrality_top,
        "more",
        title="Association Centrality",
        alt_text="Horizontal bars rank non-segment songs by eigenvector centrality on the Jaccard co-occurrence graph.",
        caption_hint="Co-occurrence centrality normalized away from raw frequency.",
        data_source="Bundled show-level song co-occurrence.",
        statistic="Eigenvector centrality over Jaccard-normalized show co-occurrence.",
        exclusion_rule="Generic segment markers are excluded.",
        claim_class="exploratory",
        dataset=datasets.centrality_top20,
    ),
    FigureSpec(
        "releases_timeline.png",
        (9, 4),
        panels.draw_releases_timeline,
        "more",
        title="Release Timeline",
        alt_text="Timeline scatterplot of releases grouped by kind.",
        caption_hint="Bundled release records by kind and date.",
        data_source="Bundled release metadata.",
        statistic="Release dates and counts by release kind.",
        exclusion_rule="Release rows do not alter performance counts.",
        dataset=datasets.releases_timeline,
    ),
    FigureSpec(
        "context_timeline.png",
        (9.5, 4.5),
        panels.draw_context_timeline,
        "more",
        apply_style=False,
        title="Historical Context Timeline",
        alt_text="Shows-per-year bar chart overlaid with selected historical milestones.",
        caption_hint="Computed show counts with cited contextual milestones; milestones are not data rows.",
        data_source="Bundled show table plus checked contextual sources.",
        statistic="Annual show counts with selected labelled historical waypoints.",
        exclusion_rule="Context labels are interpretive overlays and are not ingested rows.",
        dataset=datasets.context_timeline,
    ),
    FigureSpec(
        "tours_top.png",
        (8, 5),
        panels.draw_tours_top,
        "more",
        title="Top Tours",
        alt_text="Horizontal bar chart of top tour labels by show count.",
        caption_hint="Tour labels when available in the loaded data tier.",
        data_source="Bundled show metadata.",
        statistic="Show counts by displayed tour-label bucket.",
        exclusion_rule="Shows without tour metadata remain in the untagged bucket.",
        dataset=datasets.tours_top,
    ),
    FigureSpec(
        "bustouts.png",
        (8, 5),
        panels.draw_bustouts,
        "more",
        title="Recurrence Gaps",
        alt_text="Horizontal bar chart of songs with the widest recurrence gaps.",
        caption_hint="Largest intervening-show gaps between successive performances.",
        data_source="Chronological show order and bundled performance rows.",
        statistic="Maximum intervening-show gap between successive performances.",
        exclusion_rule="Generic segment markers are excluded.",
        dataset=datasets.bustouts_dataset,
    ),
    FigureSpec(
        "song_lifespans.png",
        (8, 6),
        panels.draw_song_lifespans,
        "more",
        title="Song Lifespans",
        alt_text="Range chart showing first-to-last performance years for selected songs.",
        caption_hint="First and last performance years for top repertoire items.",
        data_source="Bundled performance rows and era labels.",
        statistic="First-to-last performance year for top songs by performance count.",
        exclusion_rule="Generic segment markers are excluded.",
        dataset=datasets.song_lifespans,
    ),
    FigureSpec(
        "repertoire_embedding.png",
        (8.5, 5.5),
        panels.draw_repertoire_embedding,
        "more",
        title="Exploratory Repertoire Embedding",
        alt_text="Scatterplot places top non-segment songs by centered SVD era-count profiles, with cluster colors and labels only on the highest-count songs.",
        caption_hint="Exploratory pattern-discovery view; axes are SVD components, not causal dimensions.",
        data_source="Bundled performance rows and era labels.",
        statistic="Centered SVD coordinates and deterministic cluster labels over era-by-song performance profiles.",
        exclusion_rule="Generic segment markers are excluded.",
        claim_class="exploratory",
        dataset=datasets.repertoire_embedding,
    ),
    FigureSpec(
        "concentration_uncertainty.png",
        (8, 4.5),
        panels.draw_concentration_uncertainty,
        "more",
        title="Concentration Uncertainty",
        alt_text="Four horizontal error bars show fixed-seed bootstrap intervals for song and venue Gini and top-decile share.",
        caption_hint="Exploratory item-level bootstrap intervals for Gini and top-decile concentration.",
        data_source="Bundled song-performance and venue-show count vectors.",
        statistic="Fixed-seed bootstrap intervals for Gini and top-decile share.",
        exclusion_rule="Song rows exclude generic segment markers; venue rows use source-derived venue slugs.",
        claim_class="exploratory",
        dataset=datasets.concentration_uncertainty,
    ),
    FigureSpec(
        "transition_sensitivity.png",
        (8.5, 4.8),
        panels.draw_transition_sensitivity,
        "more",
        title="Transition Sensitivity",
        alt_text="Line chart compares how many transition edges and predecessor rows remain as support thresholds increase, with segment markers included versus excluded.",
        caption_hint="Descriptive support-threshold sensitivity for first-order transition models.",
        data_source="Ordered bundled performance rows and segment-marker policy.",
        statistic="Supported transition-edge and predecessor-row retention by minimum predecessor support.",
        exclusion_rule="Compares generic segment markers included versus excluded.",
        claim_class="exploratory",
        dataset=datasets.transition_sensitivity,
    ),
    FigureSpec(
        "repertoire_topn_sensitivity.png",
        (8.5, 4.8),
        panels.draw_repertoire_topn_sensitivity,
        "more",
        title="Repertoire Top-N Sensitivity",
        alt_text="Line and band chart shows how top-N song cuts cover total non-segment performances and how coverage varies across eras.",
        caption_hint="Descriptive sensitivity for alternate top-song cuts.",
        data_source="Bundled performance rows and era labels.",
        statistic="Top-N performance share plus minimum, mean, and maximum era coverage.",
        exclusion_rule="Generic segment markers are excluded.",
        claim_class="exploratory",
        dataset=datasets.repertoire_topn_sensitivity,
    ),
    FigureSpec(
        "venue_identity_review.png",
        (8.5, 4.8),
        panels.draw_venue_identity_review,
        "more",
        title="Venue Identity Review",
        alt_text="Horizontal bars summarize venue slugs, alias slugs, conservative collapses, and ambiguous same-date canonical collisions.",
        caption_hint="Report-only venue alias and ambiguity diagnostics; no venue rows are rewritten.",
        data_source="Venue table, show table, performance rows, and curated venue alias map.",
        statistic="Venue alias counts, post-canonicalization count, ambiguous collision count, and mean collision Jaccard.",
        exclusion_rule="Conservative alias review only; negative controls remain distinct.",
        claim_class="validation",
        dataset=datasets.venue_identity_review,
    ),
    FigureSpec(
        "era_repertoire_heatmap.png",
        (9.5, 5.5),
        panels.draw_era_repertoire_heatmap,
        "more",
        title="Era Repertoire Heatmap",
        alt_text="Heatmap shows each era's performance-row share for top non-segment songs, with brighter cells marking era-specific concentration.",
        caption_hint="Era-by-song normalized intensity over non-segment performance rows.",
        data_source="Bundled performance rows and era labels.",
        statistic="Within-era performance-row share by top song.",
        exclusion_rule="Generic segment markers are excluded.",
        claim_class="exploratory",
        dataset=datasets.era_repertoire_heatmap,
    ),
    FigureSpec(
        "claim_evidence_matrix.png",
        (8.8, 4.8),
        panels.draw_claim_evidence_matrix,
        "more",
        apply_style=False,
        title="First-Principles Claim Evidence Map",
        alt_text="Heatmap counts claim families by claim class and primary validation artifact family, distinguishing corpus, method, boundary, and interpretation claims.",
        caption_hint="Evidence-governance matrix; cells count claim families, not corpus observations.",
        data_source="First-principles claim ledger generated from compendium contracts and reports.",
        statistic="Claim-family counts by claim class and validation artifact family.",
        exclusion_rule="Counts claim families, not shows, performances, songs, or venues.",
        claim_class="validation",
        dataset=datasets.claim_evidence_matrix,
    ),
)

MOSAIC_FILENAME = "mosaic.png"
ALLUVIAL_FILENAME = "alluvial_composer_song_era.png"
ALLUVIAL_TOP_PATHS = 40

EXPECTED_FILENAMES: tuple[str, ...] = tuple(spec.filename for spec in FIGURE_SPECS) + (
    MOSAIC_FILENAME,
    ALLUVIAL_FILENAME,
)

DASHBOARD_FIGURES: tuple[str, ...] = (MOSAIC_FILENAME,) + tuple(
    spec.filename for spec in FIGURE_SPECS if spec.dashboard
)

FIGURE_SPEC_BY_FILENAME: dict[str, FigureSpec] = {
    spec.filename: spec for spec in FIGURE_SPECS
}


def specs_for_group(group: FigureGroup) -> tuple[FigureSpec, ...]:
    return tuple(spec for spec in FIGURE_SPECS if spec.group == group)


def render_one(spec: FigureSpec, comp: Compendium, out_dir: Path) -> Path | None:
    """Render a single panel figure; return ``None`` when the draw helper skips."""
    fig, ax = plt.subplots(figsize=spec.figsize)
    result = spec.draw(ax, comp)
    if result is False:
        plt.close(fig)
        return None
    if spec.apply_style:
        style.style_axes(ax)
    fig.tight_layout()
    return panels.save_figure(fig, out_dir / spec.filename, comp=comp)


def render_group(comp: Compendium, out_dir: Path, group: FigureGroup) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for spec in specs_for_group(group):
        path = render_one(spec, comp, out_dir)
        if path is not None:
            paths.append(path)
            print(path)
    return paths


def render_all_panels(comp: Compendium, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for spec in FIGURE_SPECS:
        path = render_one(spec, comp, out_dir)
        if path is not None:
            paths.append(path)
            print(path)
    return paths
