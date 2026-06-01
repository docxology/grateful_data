"""First-principles evidence ledger for manuscript claim governance.

The ledger is not another statistical model. It is a compact, executable
mapping from claim families to the irreducible inputs, constraints, assumptions,
validation artifacts, and interpretation limits that make those claims honest.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from ..integration.reconcile import Compendium

ARTIFACT_FAMILIES: tuple[str, ...] = (
    "schema/data",
    "analysis/report",
    "figure/data",
    "validation/test",
    "citation/prose",
)

CLAIM_CLASSES: tuple[str, ...] = (
    "Descriptive",
    "Structural",
    "Exploratory",
    "Formal",
    "Contextual",
    "Boundary",
)

CLAIM_METADATA: dict[str, dict[str, str]] = {
    "Corpus scope and identity": {
        "manuscript_section": "Data and Scope",
        "figure_filename": "not-applicable",
        "report_key": "analysis_report.json::top_line",
        "test_file": "tests/test_pipeline_integration.py",
        "claim_status": "audited-descriptive",
    },
    "Setlist-size distribution": {
        "manuscript_section": "Descriptive Statistics",
        "figure_filename": "performance_distribution.png",
        "report_key": "analysis_report.json::performance_distribution",
        "test_file": "tests/test_distributions.py",
        "claim_status": "audited-descriptive",
    },
    "Repertoire ranking": {
        "manuscript_section": "Repertoire Shape",
        "figure_filename": "top_songs.png",
        "report_key": "analysis_report.json::top_songs",
        "test_file": "tests/test_stats.py",
        "claim_status": "audited-descriptive",
    },
    "Concentration metrics": {
        "manuscript_section": "Concentration and Uncertainty",
        "figure_filename": "concentration_uncertainty.png",
        "report_key": "analysis_report.json::concentration_uncertainty",
        "test_file": "tests/test_distributions.py",
        "claim_status": "audited-model",
    },
    "Transition model": {
        "manuscript_section": "Transitions and Segues",
        "figure_filename": "transition_matrix.png",
        "report_key": "analysis_report.json::transition_significance",
        "test_file": "tests/test_transitions.py",
        "claim_status": "audited-model",
    },
    "Explicit segue structure": {
        "manuscript_section": "Transitions and Segues",
        "figure_filename": "segue_graph.png",
        "report_key": "analysis_report.json::segues",
        "test_file": "tests/test_more_analyses.py",
        "claim_status": "audited-descriptive",
    },
    "Co-occurrence and centrality": {
        "manuscript_section": "Co-occurrence",
        "figure_filename": "cooccurrence_heatmap.png",
        "report_key": "analysis_report.json::cooccurrence",
        "test_file": "tests/test_more_analyses.py",
        "claim_status": "audited-model",
    },
    "Exploratory repertoire embedding": {
        "manuscript_section": "Exploratory Repertoire Geometry",
        "figure_filename": "repertoire_embedding.png",
        "report_key": "analysis_report.json::exploratory_repertoire",
        "test_file": "tests/test_exploratory.py",
        "claim_status": "exploratory-noncausal",
    },
    "Category-theoretic abstraction": {
        "manuscript_section": "Categorical Model",
        "figure_filename": "functor_cardinalities.png",
        "report_key": "category_theory_report.json",
        "test_file": "tests/test_category_theory.py",
        "claim_status": "audited-formalization",
    },
    "Venue geography": {
        "manuscript_section": "Geography",
        "figure_filename": "geo_scatter.png",
        "report_key": "analysis_report.json::venue_geography",
        "test_file": "tests/test_more_analyses.py",
        "claim_status": "metadata-limited",
    },
    "Lyrics and review overlays": {
        "manuscript_section": "External Pointer Overlays",
        "figure_filename": "lyric_themes.png",
        "report_key": "analysis_report.json::lyrics_reviews",
        "test_file": "tests/test_lyric_enrichment.py",
        "claim_status": "pointer-only-limited",
    },
    "Historical and archival context": {
        "manuscript_section": "Related Work and Archival Context",
        "figure_filename": "context_timeline.png",
        "report_key": "bibliography_report.json",
        "test_file": "tests/test_fetch_bibliography.py",
        "claim_status": "citation-supported",
    },
}


@dataclass(frozen=True)
class ClaimEvidence:
    """One claim family and the evidence boundaries behind it."""

    claim_area: str
    claim_class: str
    irreducible_input: str
    hard_constraint: str
    soft_constraint: str
    assumption: str
    validation_artifact: str
    artifact_family: str
    interpretation_limit: str
    figure_or_report: str

    def __post_init__(self) -> None:
        if self.claim_class not in CLAIM_CLASSES:
            raise ValueError(f"unknown claim class: {self.claim_class}")
        if self.artifact_family not in ARTIFACT_FAMILIES:
            raise ValueError(f"unknown artifact family: {self.artifact_family}")
        for field, value in self.to_dict().items():
            if not str(value).strip():
                raise ValueError(f"{field} must be non-empty")

    def to_dict(self) -> dict[str, str]:
        metadata = CLAIM_METADATA.get(
            self.claim_area,
            {
                "manuscript_section": "unmapped",
                "figure_filename": "unmapped",
                "report_key": "unmapped",
                "test_file": "unmapped",
                "claim_status": "unmapped",
            },
        )
        return {
            "claim_area": self.claim_area,
            "claim_class": self.claim_class,
            "irreducible_input": self.irreducible_input,
            "hard_constraint": self.hard_constraint,
            "soft_constraint": self.soft_constraint,
            "assumption": self.assumption,
            "validation_artifact": self.validation_artifact,
            "artifact_family": self.artifact_family,
            "interpretation_limit": self.interpretation_limit,
            "figure_or_report": self.figure_or_report,
            **metadata,
        }


def claim_evidence_rows(compendium: Compendium) -> tuple[ClaimEvidence, ...]:
    """Return the deterministic claim ledger for the loaded compendium."""
    n_shows = len(compendium.shows)
    n_performances = len(compendium.performances)
    n_songs = len(compendium.songs)
    n_venues = len(compendium.venues)
    n_segues = sum(1 for perf in compendium.performances if perf.segue_into)
    return (
        ClaimEvidence(
            claim_area="Corpus scope and identity",
            claim_class="Descriptive",
            irreducible_input=f"{n_shows} Show rows, {n_performances} Performance rows, {n_songs} Song rows",
            hard_constraint="Every hard foreign key resolves before analyses run",
            soft_constraint="Venue and song slugs normalize names but do not prove real-world identity",
            assumption="The committed archival snapshot is the publication baseline",
            validation_artifact="completeness_report.json; src/validation.py; raw entity exports",
            artifact_family="schema/data",
            interpretation_limit="Referential completeness is not exhaustive coverage of every concert or optional layer",
            figure_or_report="analysis_report.json::top_line",
        ),
        ClaimEvidence(
            claim_area="Setlist-size distribution",
            claim_class="Descriptive",
            irreducible_input="Per-show counts of ordered Performance rows, including zero-row shows",
            hard_constraint="Empty setlists remain in the denominator",
            soft_constraint="Set and position fields are source-derived ordering metadata",
            assumption="A performance row is a setlist-entry unit, not a duration unit",
            validation_artifact="performance_distribution figure dataset and distribution tests",
            artifact_family="analysis/report",
            interpretation_limit="The statistic describes metadata density, not musical length or quality",
            figure_or_report="performance_distribution.png",
        ),
        ClaimEvidence(
            claim_area="Repertoire ranking",
            claim_class="Descriptive",
            irreducible_input="Song performance counts after generic segment-marker exclusion",
            hard_constraint="drums, space, tuning, feedback, and jam markers are surfaced but excluded from song rankings",
            soft_constraint="Canonical song aliases are conservative and title-based",
            assumption="Segment markers are set structure rather than repertoire items",
            validation_artifact="analysis_report.json::segment_marker_counts; top_songs dataset",
            artifact_family="figure/data",
            interpretation_limit="A high count is not a preference, importance, or aesthetic claim",
            figure_or_report="top_songs.png",
        ),
        ClaimEvidence(
            claim_area="Concentration metrics",
            claim_class="Descriptive",
            irreducible_input="Ranked song-performance counts and venue-show counts",
            hard_constraint="Gini and top-decile statistics are computed from observed item counts only",
            soft_constraint="Bootstrap intervals resample items with a fixed deterministic seed",
            assumption="Item-level resampling is an uncertainty display, not a population model",
            validation_artifact="concentration_uncertainty_report; bootstrap interval tests",
            artifact_family="analysis/report",
            interpretation_limit="Intervals do not estimate unseen concerts or listener behavior",
            figure_or_report="concentration_uncertainty.png",
        ),
        ClaimEvidence(
            claim_area="Transition model",
            claim_class="Structural",
            irreducible_input="Adjacent within-show Performance rows",
            hard_constraint="Only first-order next-song transitions are modeled",
            soft_constraint="Permutation screening controls false discoveries for supported cells",
            assumption="Within-show adjacency is meaningful setlist structure",
            validation_artifact="transition_significance_summary with Benjamini-Hochberg FDR control",
            artifact_family="analysis/report",
            interpretation_limit="Transition probabilities are not causal or predictive laws",
            figure_or_report="transition_matrix.png",
        ),
        ClaimEvidence(
            claim_area="Explicit segue structure",
            claim_class="Structural",
            irreducible_input=f"{n_segues} source-marked segue_into edges",
            hard_constraint="Only explicit source markers create segue edges",
            soft_constraint="Unmarked adjacency remains visible in the transition model",
            assumption="Source segue notation is sparse but semantically stronger than plain adjacency",
            validation_artifact="segue_edges output and segue_graph figure dataset",
            artifact_family="figure/data",
            interpretation_limit="Unmarked segues and audio-continuity evidence are outside this corpus",
            figure_or_report="segue_graph.png",
        ),
        ClaimEvidence(
            claim_area="Co-occurrence and centrality",
            claim_class="Structural",
            irreducible_input="Show-by-song presence matrix",
            hard_constraint="Centrality uses Jaccard-normalized co-occurrence rather than raw frequency",
            soft_constraint="Top-song heatmaps are size-limited for legibility",
            assumption="Show-level co-presence is a useful association signal",
            validation_artifact="cooccurrence_matrix tests; centrality figure dataset",
            artifact_family="figure/data",
            interpretation_limit="Association centrality is not influence, authorship, or musical similarity",
            figure_or_report="cooccurrence_heatmap.png; centrality_top20.png",
        ),
        ClaimEvidence(
            claim_area="Exploratory repertoire embedding",
            claim_class="Exploratory",
            irreducible_input="Era-by-song log-count profiles with segment markers excluded",
            hard_constraint="Centered SVD and deterministic clustering use fixed seeds and stable tie-breaks",
            soft_constraint="Top-N songs are selected to keep labels readable at manuscript size",
            assumption="Era-weighted count profiles can reveal inspectable repertoire neighborhoods",
            validation_artifact="exploratory_repertoire_report and deterministic clustering tests",
            artifact_family="analysis/report",
            interpretation_limit="Clusters are pattern-discovery aids, not definitive musicological taxonomy",
            figure_or_report="repertoire_embedding.png; era_repertoire_heatmap.png",
        ),
        ClaimEvidence(
            claim_area="Category-theoretic abstraction",
            claim_class="Formal",
            irreducible_input="Finite date poset, performance spans, and lineup intervals",
            hard_constraint="Functor monotonicity and naturality checks are machine-evaluated",
            soft_constraint="The abstraction preserves incidence and cumulative cardinality, not audio semantics",
            assumption="Setlists and lineups can be modeled as finite categorical structures",
            validation_artifact="category_theory_report.json and negative-control tests",
            artifact_family="validation/test",
            interpretation_limit="Formal coherence does not prove cultural or musical explanation",
            figure_or_report="functor_cardinalities.png",
        ),
        ClaimEvidence(
            claim_area="Venue geography",
            claim_class="Descriptive",
            irreducible_input=f"{n_venues} venue slugs plus committed geo sidecar rows",
            hard_constraint="Figures use only venues with resolved coordinates",
            soft_constraint="Alias collapse is precision-oriented and intentionally incomplete",
            assumption="Venue-level aggregation is the appropriate unit for geographic views",
            validation_artifact="geo_scatter figure dataset; completeness venue-geo check",
            artifact_family="figure/data",
            interpretation_limit="Slug-level venue counts are lower bounds per physical building when aliases remain",
            figure_or_report="geo_scatter.png",
        ),
        ClaimEvidence(
            claim_area="Lyrics and review overlays",
            claim_class="Boundary",
            irreducible_input="LyricPointer URLs, curated theme tags, and sourced review sentiment rows",
            hard_constraint="No lyric text or audio features are bundled",
            soft_constraint="Theme and sentiment overlays are curated/partial by design",
            assumption="Pointers can support metadata-level interpretation without reproducing protected text",
            validation_artifact="HonestyBoundary; lyric_themes and sentiment_by_kind datasets",
            artifact_family="validation/test",
            interpretation_limit="Overlay counts are not representative samples of all lyrics or reviews",
            figure_or_report="lyric_themes.png; sentiment_by_kind.png",
        ),
        ClaimEvidence(
            claim_area="Historical and archival context",
            claim_class="Contextual",
            irreducible_input="Stable citation keys and cited contextual milestones",
            hard_constraint="Contextual sources do not create Show, Performance, or Recording rows",
            soft_constraint="Timeline milestones are selected orientation anchors",
            assumption="Official, archival, and scholarly sources are stronger anchors than secondary summaries",
            validation_artifact="references.bib; bibliography parser; rendered citation checks",
            artifact_family="citation/prose",
            interpretation_limit="Contextual overlays explain why dates matter but do not alter computed counts",
            figure_or_report="context_timeline.png; citation_kinds.png",
        ),
    )


def claim_evidence_matrix(
    compendium: Compendium,
) -> tuple[tuple[int, ...], tuple[str, ...], tuple[str, ...]]:
    """Count evidence-ledger rows by claim class and artifact family."""
    counts = Counter(
        (row.claim_class, row.artifact_family) for row in claim_evidence_rows(compendium)
    )
    matrix = tuple(
        tuple(counts.get((claim_class, family), 0) for family in ARTIFACT_FAMILIES)
        for claim_class in CLAIM_CLASSES
    )
    return matrix, CLAIM_CLASSES, ARTIFACT_FAMILIES


def review_summary(compendium: Compendium) -> dict[str, object]:
    """JSON-serializable first-principles review payload."""
    rows = claim_evidence_rows(compendium)
    matrix, claim_classes, artifact_families = claim_evidence_matrix(compendium)
    hard_constraints = {row.hard_constraint for row in rows}
    soft_constraints = {row.soft_constraint for row in rows}
    assumptions = {row.assumption for row in rows}
    artifacts = {row.validation_artifact for row in rows}
    return {
        "method": "First-principles claim ledger: deconstruct claims into inputs, constraints, assumptions, evidence artifacts, and limits.",
        "n_claim_areas": len(rows),
        "n_claim_classes": len({row.claim_class for row in rows}),
        "n_hard_constraints": len(hard_constraints),
        "n_soft_constraints": len(soft_constraints),
        "n_assumptions": len(assumptions),
        "n_validation_artifacts": len(artifacts),
        "claim_classes": list(claim_classes),
        "artifact_families": list(artifact_families),
        "matrix": [
            {
                "claim_class": claim_class,
                "counts": {
                    family: matrix[row_idx][col_idx]
                    for col_idx, family in enumerate(artifact_families)
                },
            }
            for row_idx, claim_class in enumerate(claim_classes)
        ],
        "rows": [row.to_dict() for row in rows],
    }


def write_review(compendium: Compendium, out_dir: Path) -> tuple[Path, Path]:
    """Write JSON and CSV evidence ledgers under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = claim_evidence_rows(compendium)
    json_path = out_dir / "first_principles_review.json"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(review_summary(compendium), fh, indent=2, sort_keys=True)
        fh.write("\n")
    csv_path = out_dir / "first_principles_claims.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=tuple(rows[0].to_dict()))
        writer.writeheader()
        writer.writerows(row.to_dict() for row in rows)
    return json_path, csv_path
