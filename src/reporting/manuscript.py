"""Manuscript variable derivation and template hydration for PDF render.

Moved verbatim from ``scripts/z_generate_manuscript_variables.py`` so the
derivation logic is importable and testable; the script is a thin wrapper
around :func:`main`.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from src.audit import FULL_CORPUS_SHOW_ESTIMATE, audit_completeness
from src.seed import load_seed_compendium

ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = ROOT / "data" / "seed"
_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def find_template_root(start: Path) -> Path:
    env = os.environ.get("TEMPLATE_REPO_ROOT", "").strip()
    if env:
        root = Path(env)
        if (root / "infrastructure" / "rendering").is_dir():
            return root
    for candidate in (start, *start.parents):
        if (candidate / "infrastructure" / "rendering").is_dir():
            return candidate
        # Private checkout: template repo checked out beside any ancestor
        # (e.g. <Git>/template beside <Git>/projects/<lifecycle>/<org>/<repo>).
        sibling = candidate / "template"
        if (sibling / "infrastructure" / "rendering").is_dir():
            return sibling
    raise OSError(
        "template repo root not found (set TEMPLATE_REPO_ROOT or run from template checkout)"
    )


def _seed_overlay_counts() -> dict[str, str]:
    """Pinned curated exemplar counts (always from ``data/seed/`` overlay files)."""

    def _count(filename: str) -> int:
        path = SEED_DIR / filename
        if not path.is_file():
            return 0
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return len(data) if isinstance(data, list) else 0

    return {
        "CURATED_REVIEWS_N": str(_count("reviews.json")),
        "CURATED_CITATIONS_N": str(_count("citations.json")),
        "CURATED_LYRIC_POINTERS_N": str(_count("lyric_pointers.json")),
        "CURATED_RELEASES_N": str(_count("releases.json")),
    }


def _top_song_fields(analysis: dict) -> dict[str, str]:
    top3 = analysis.get("top_songs_top3") or analysis.get("top_songs") or []
    out: dict[str, str] = {
        "TOP_SONG": "",
        "TOP_SONG_COUNT": "0",
        "TOP_SONG_2": "",
        "TOP_SONG_2_COUNT": "0",
        "TOP_SONG_3": "",
        "TOP_SONG_3_COUNT": "0",
    }
    for idx, row in enumerate(top3[:3]):
        slug = str(row.get("slug", ""))
        count = str(row.get("count", 0))
        if idx == 0:
            out["TOP_SONG"] = slug
            out["TOP_SONG_COUNT"] = count
        elif idx == 1:
            out["TOP_SONG_2"] = slug
            out["TOP_SONG_2_COUNT"] = count
        else:
            out["TOP_SONG_3"] = slug
            out["TOP_SONG_3_COUNT"] = count
    if analysis.get("top_song"):
        out["TOP_SONG"] = str(analysis["top_song"])
    if analysis.get("top_song_count") is not None:
        out["TOP_SONG_COUNT"] = str(analysis["top_song_count"])
    return out


def _corpus_scope_phrase(shows: str, songs: str, venues: str, perfs: str) -> str:
    return (
        f"{shows} ingested shows (gdshowsdb + truckin gap-fill; community literature "
        f"estimates ~{FULL_CORPUS_SHOW_ESTIMATE} canonical concerts), "
        f"{songs} songs, {venues} venues, {perfs} performance rows"
    )


def _fmt_number(value: object, *, digits: int = 2) -> str:
    """Compact decimal string for manuscript variables."""
    if value in (None, ""):
        return ""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if num.is_integer():
        return str(int(num))
    return f"{num:.{digits}f}".rstrip("0").rstrip(".")


def _figure_dataset_fields(comp) -> dict[str, str]:
    """Derive caption-facing counts from registered figure dataset exporters."""

    from src.viz import figures as _figures  # noqa: PLC0415

    cache: dict[str, object] = {}

    def _dataset(filename: str):
        if filename not in cache:
            spec = _figures.FIGURE_SPEC_BY_FILENAME[filename]
            if spec.dataset is None:
                cache[filename] = None
            else:
                cache[filename] = spec.dataset(comp)
        return cache[filename]

    def _n_rows(filename: str) -> str:
        dataset = _dataset(filename)
        return str(len(dataset.rows)) if dataset is not None else "0"

    def _n_unique(filename: str, column: str) -> str:
        dataset = _dataset(filename)
        if dataset is None:
            return "0"
        try:
            idx = dataset.columns.index(column)
        except ValueError:
            return "0"
        return str(len({row[idx] for row in dataset.rows}))

    return {
        "FIG_TOP_SONGS_N": _n_rows("top_songs.png"),
        "FIG_COOCCURRENCE_SONG_N": _n_unique(
            "cooccurrence_heatmap.png", "source_song_slug"
        ),
        "FIG_TRANSITION_SONG_N": _n_unique(
            "transition_matrix.png", "previous_song_slug"
        ),
        "FIG_STATIONARY_N": _n_rows("stationary_top20.png"),
        "FIG_CENTRALITY_N": _n_rows("centrality_top20.png"),
        "FIG_COMPOSER_N": _n_rows("composer_attribution.png"),
        "FIG_ERA_DENSITY_CELL_N": _n_rows("era_density.png"),
        "FIG_PERSONNEL_INTERVAL_N": _n_rows("personnel_gantt.png"),
        "FIG_ERA_LABEL_N": _n_rows("shows_by_era.png"),
        "FIG_LINEUP_DATE_N": _n_rows("lineup_diversity.png"),
        "FIG_REVIEW_KIND_N": _n_rows("sentiment_by_kind.png"),
        "FIG_CITATION_KIND_N": _n_rows("citation_kinds.png"),
        "FIG_RECORDING_SOURCE_TYPE_N": _n_rows("recording_sources.png"),
        "FIG_LYRIC_THEME_N": _n_rows("lyric_themes.png"),
        "FIG_SEGUE_EDGE_N": _n_rows("segue_graph.png"),
        "FIG_GEO_VENUE_N": _n_rows("geo_scatter.png"),
        "FIG_SET_POSITION_N": _n_rows("set_positions.png"),
        "FIG_TOUR_LABEL_N": _n_rows("tours_top.png"),
        "FIG_BUSTOUT_N": _n_rows("bustouts.png"),
        "FIG_LIFESPAN_N": _n_rows("song_lifespans.png"),
        "FIG_RELEASE_N": _n_rows("releases_timeline.png"),
        "ALLUVIAL_TOP_PATHS_N": str(_figures.ALLUVIAL_TOP_PATHS),
    }


def _write_counts() -> dict[str, str]:
    comp = load_seed_compendium()
    dates = sorted(s.date.isoformat() for s in comp.shows)
    n_shows = len(comp.shows)
    payload: dict[str, str] = {
        "CORPUS_LABEL": "archival compendium",
        "INGESTED_SHOWS_N": str(n_shows),
        "ARCHIVAL_SHOWS": str(n_shows),
        "ARCHIVAL_SONGS": str(len(comp.songs)),
        "ARCHIVAL_PERFORMANCES": str(len(comp.performances)),
        "ARCHIVAL_VENUES": str(len(comp.venues)),
        "ARCHIVAL_PEOPLE": str(len(comp.people)),
        "ARCHIVAL_RECORDINGS": str(len(comp.recordings)),
        "ARCHIVAL_SEGUE_MARKERS": str(
            sum(1 for p in comp.performances if p.segue_into)
        ),
        "FULL_CORPUS_SHOW_ESTIMATE": str(FULL_CORPUS_SHOW_ESTIMATE),
        "ARCHIVAL_DATE_MIN": dates[0] if dates else "",
        "ARCHIVAL_DATE_MAX": dates[-1] if dates else "",
        "REVIEWS_N": str(len(comp.reviews)),
        "CITATIONS_N": str(len(comp.citations)),
        "LYRIC_POINTERS_N": str(len(comp.lyric_pointers)),
        "RELEASES_N": str(len(comp.releases)),
    }
    payload.update(_seed_overlay_counts())
    completeness = audit_completeness(comp)
    payload["MAXIMINUS_REVIEWS_N"] = str(completeness.maximinus_reviews_n)
    payload["CURATED_ARCHIVAL_REVIEWS_N"] = str(completeness.curated_reviews_n)
    payload["LYRIC_POINTERS_WITH_LYRICIST_N"] = str(
        completeness.songs_with_lyricist_on_pointer
    )
    payload["LYRIC_POINTERS_WITH_THEMES_N"] = str(
        completeness.songs_with_themes_on_pointer
    )
    payload["SONGS_WITHOUT_LYRIC_POINTER_N"] = str(
        completeness.performed_songs_without_lyric_pointer
    )
    payload["SHOWS_WITHOUT_PERFORMANCES_N"] = str(
        len(completeness.shows_without_performances)
    )
    analysis_path = ROOT / "output" / "reports" / "analysis_report.json"
    if analysis_path.exists():
        with analysis_path.open("r", encoding="utf-8") as fh:
            analysis = json.load(fh)
        payload.update(_top_song_fields(analysis))
    cat_path = ROOT / "output" / "reports" / "category_theory_report.json"
    if cat_path.exists():
        with cat_path.open("r", encoding="utf-8") as fh:
            cat = json.load(fh)
        payload["CUMULATIVE_SETLIST_CARD_END"] = str(
            cat.get("cumulative_setlist_cardinality_end", "")
        )
        payload["CUMULATIVE_LINEUP_CARD_END"] = str(
            cat.get("cumulative_lineup_cardinality_end", "")
        )
    # Figure count is registry-derived so the manuscript never goes stale.
    from src.viz import figures as _figures  # noqa: PLC0415

    payload["N_FIGURES"] = str(len(_figures.EXPECTED_FILENAMES))
    payload.update(_figure_dataset_fields(comp))
    figure_index_path = ROOT / "output" / "data" / "figures" / "index.json"
    if figure_index_path.exists():
        with figure_index_path.open("r", encoding="utf-8") as fh:
            figure_index = json.load(fh)
        payload["FIGURE_DATASETS_N"] = str(figure_index.get("n_datasets", ""))
    else:
        payload["FIGURE_DATASETS_N"] = "0"
    fp_path = ROOT / "output" / "reports" / "first_principles_review.json"
    if fp_path.exists():
        with fp_path.open("r", encoding="utf-8") as fh:
            fp_review = json.load(fh)
        payload["FIRST_PRINCIPLES_CLAIM_AREAS_N"] = str(
            fp_review.get("n_claim_areas", "")
        )
        payload["FIRST_PRINCIPLES_CLAIM_CLASSES_N"] = str(
            fp_review.get("n_claim_classes", "")
        )
        payload["FIRST_PRINCIPLES_HARD_CONSTRAINTS_N"] = str(
            fp_review.get("n_hard_constraints", "")
        )
        payload["FIRST_PRINCIPLES_ASSUMPTIONS_N"] = str(
            fp_review.get("n_assumptions", "")
        )
        payload["FIRST_PRINCIPLES_VALIDATION_ARTIFACTS_N"] = str(
            fp_review.get("n_validation_artifacts", "")
        )
    else:
        payload["FIRST_PRINCIPLES_CLAIM_AREAS_N"] = "0"
        payload["FIRST_PRINCIPLES_CLAIM_CLASSES_N"] = "0"
        payload["FIRST_PRINCIPLES_HARD_CONSTRAINTS_N"] = "0"
        payload["FIRST_PRINCIPLES_ASSUMPTIONS_N"] = "0"
        payload["FIRST_PRINCIPLES_VALIDATION_ARTIFACTS_N"] = "0"
    analysis_path2 = ROOT / "output" / "reports" / "analysis_report.json"
    if analysis_path2.exists():
        with analysis_path2.open("r", encoding="utf-8") as fh:
            adata = json.load(fh)
        cov = adata.get("catalog_coverage", {})
        payload["CATALOG_COVERAGE_PCT"] = str(cov.get("coverage_pct", ""))
        payload["N_NEVER_PERFORMED"] = str(cov.get("n_never_performed", ""))
        payload["N_PERFORMED_IN_CATALOG"] = str(cov.get("n_performed_in_catalog", ""))
        payload["N_SIGNIFICANT_TRANSITIONS"] = str(
            adata.get("significant_transitions_n", "")
        )
        tsig = adata.get("transition_significance", {})
        payload["N_TRANSITIONS_UNCORRECTED"] = str(tsig.get("n_uncorrected", ""))
        payload["N_TRANSITION_CANDIDATES"] = str(tsig.get("n_candidates", ""))
        # Distinct date-poset objects, for the category-theory prose (was a
        # hardcoded "roughly 2,300" — see RedTeam iter-8 CE on stale literals).
        payload["N_DATE_POSET_OBJECTS"] = str(adata.get("date_poset_objects", ""))
        seg = adata.get("segue_summary", {})
        payload["N_SEGUE_EDGES"] = str(seg.get("n_distinct_edges", ""))
        payload["TOP_SEGUE_SRC"] = str(seg.get("top_segue_src", ""))
        payload["TOP_SEGUE_DST"] = str(seg.get("top_segue_dst", ""))
        payload["TOP_SEGUE_COUNT"] = str(seg.get("top_segue_count", ""))
        payload["TOP_SEGUE_OUT_SONG"] = str(seg.get("top_out_degree_song", ""))
        payload["TOP_SEGUE_OUT_COUNT"] = str(seg.get("top_out_degree_count", ""))
        vdup = adata.get("venue_duplication", {})
        payload["N_VENUE_DUP_COLLAPSED"] = str(vdup.get("n_venues_collapsed", ""))
        payload["N_VENUES_AFTER_CANON"] = str(
            vdup.get("n_venues_after_canonicalization", "")
        )
        payload["N_AMBIGUOUS_VENUE_COLLISIONS"] = str(
            vdup.get("n_ambiguous_same_date_collisions", "")
        )
        payload["VENUE_DUP_MEAN_JACCARD"] = str(
            vdup.get("mean_collision_setlist_jaccard", "")
        )
        shape = adata.get("statistical_shape", {})
        perf_dist = shape.get("performance_rows_per_show", {})
        per_show = perf_dist.get("per_show", {})
        payload["PERFS_PER_SHOW_MEAN"] = _fmt_number(per_show.get("mean"))
        payload["PERFS_PER_SHOW_MEDIAN"] = _fmt_number(per_show.get("median"))
        payload["PERFS_PER_SHOW_P90"] = _fmt_number(per_show.get("p90"))
        payload["PERFS_PER_SHOW_MAX"] = _fmt_number(per_show.get("maximum"))
        payload["ZERO_PERF_SHOWS_N"] = str(
            perf_dist.get("n_zero_performance_shows", "")
        )
        song_conc = shape.get("song_performance_concentration", {})
        payload["SONG_PERF_GINI"] = _fmt_number(song_conc.get("gini"))
        payload["SONG_TOP10_SHARE_PCT"] = _fmt_number(song_conc.get("top_10_share_pct"))
        payload["SONGS_FOR_50_SHARE"] = str(song_conc.get("n_for_50_pct", ""))
        payload["SONGS_FOR_80_SHARE"] = str(song_conc.get("n_for_80_pct", ""))
        payload["SONGS_FOR_50_SHARE_PCT_ITEMS"] = _fmt_number(
            song_conc.get("pct_items_for_50_pct")
        )
        payload["SONGS_FOR_80_SHARE_PCT_ITEMS"] = _fmt_number(
            song_conc.get("pct_items_for_80_pct")
        )
        venue_conc = shape.get("venue_show_concentration", {})
        payload["VENUE_SHOW_GINI"] = _fmt_number(venue_conc.get("gini"))
        payload["VENUE_TOP10_SHARE_PCT"] = _fmt_number(
            venue_conc.get("top_10_share_pct")
        )
        payload["VENUES_FOR_50_SHARE"] = str(venue_conc.get("n_for_50_pct", ""))
        payload["VENUES_FOR_80_SHARE"] = str(venue_conc.get("n_for_80_pct", ""))
        payload["VENUES_FOR_50_SHARE_PCT_ITEMS"] = _fmt_number(
            venue_conc.get("pct_items_for_50_pct")
        )
        payload["VENUES_FOR_80_SHARE_PCT_ITEMS"] = _fmt_number(
            venue_conc.get("pct_items_for_80_pct")
        )
        uncertainty = shape.get("concentration_uncertainty", {})

        def _interval_fields(prefix: str, family: str, metric: str) -> None:
            family_payload = uncertainty.get(family, {})
            interval = (
                family_payload.get(metric, {})
                if isinstance(family_payload, dict)
                else {}
            )
            payload[f"{prefix}_POINT"] = _fmt_number(interval.get("point"), digits=3)
            payload[f"{prefix}_CI_LOW"] = _fmt_number(interval.get("low"), digits=3)
            payload[f"{prefix}_CI_HIGH"] = _fmt_number(interval.get("high"), digits=3)

        _interval_fields(
            "SONG_PERF_GINI_BOOT",
            "song_performance_concentration",
            "gini",
        )
        _interval_fields(
            "SONG_TOP10_SHARE_BOOT",
            "song_performance_concentration",
            "top_10_share_pct",
        )
        _interval_fields(
            "VENUE_SHOW_GINI_BOOT",
            "venue_show_concentration",
            "gini",
        )
        _interval_fields(
            "VENUE_TOP10_SHARE_BOOT",
            "venue_show_concentration",
            "top_10_share_pct",
        )
        topn = shape.get("repertoire_topn_sensitivity", {})
        topn_rows = topn.get("rows", []) if isinstance(topn, dict) else []
        if isinstance(topn_rows, list) and topn_rows:
            payload["REPERTOIRE_TOPN_VALUES"] = ", ".join(
                str(row.get("top_n"))
                for row in topn_rows
                if isinstance(row, dict) and row.get("top_n") is not None
            )
            last_row = next(
                (row for row in reversed(topn_rows) if isinstance(row, dict)),
                {},
            )
            payload["REPERTOIRE_TOPN_MAX_N"] = str(last_row.get("top_n", ""))
            payload["REPERTOIRE_TOPN_MAX_SHARE_PCT"] = _fmt_number(
                last_row.get("performance_share_pct")
            )
        transition_sensitivity = adata.get("transition_sensitivity", {})
        thresholds = (
            transition_sensitivity.get("support_thresholds", [])
            if isinstance(transition_sensitivity, dict)
            else []
        )
        payload["TRANSITION_SENSITIVITY_THRESHOLDS"] = ", ".join(
            str(value) for value in thresholds
        )
        exploratory = adata.get("exploratory_repertoire", {})
        payload["REPERTOIRE_EMBEDDING_SONG_N"] = str(
            exploratory.get("n_songs_embedded", "")
        )
        payload["REPERTOIRE_CLUSTER_N"] = str(exploratory.get("n_clusters", ""))
        shares = exploratory.get("component_variance_share", {})
        c1 = shares.get("component_1", "") if isinstance(shares, dict) else ""
        c2 = shares.get("component_2", "") if isinstance(shares, dict) else ""
        payload["REPERTOIRE_SVD_COMPONENT_1_SHARE_PCT"] = _fmt_number(
            float(c1) * 100.0 if c1 != "" else ""
        )
        payload["REPERTOIRE_SVD_COMPONENT_2_SHARE_PCT"] = _fmt_number(
            float(c2) * 100.0 if c2 != "" else ""
        )
        clusters = exploratory.get("clusters", [])
        if isinstance(clusters, list):
            payload["REPERTOIRE_CLUSTER_SUMMARY"] = "; ".join(
                f"C{row.get('cluster')}: {row.get('n_songs')} songs, "
                f"{row.get('dominant_era')} dominant"
                for row in clusters[:5]
                if isinstance(row, dict)
            )
    payload["CORPUS_SCOPE_PHRASE"] = _corpus_scope_phrase(
        payload["ARCHIVAL_SHOWS"],
        payload["ARCHIVAL_SONGS"],
        payload["ARCHIVAL_VENUES"],
        payload["ARCHIVAL_PERFORMANCES"],
    )
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    counts_path = out_dir / "manuscript_counts.json"
    with counts_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return payload


def _unresolved_tokens(manuscript_dir: Path) -> list[str]:
    unresolved: list[str] = []
    for path in sorted(manuscript_dir.glob("*.md")):
        if path.name in {"AGENTS.md", "README.md", "SYNTAX.md"}:
            continue
        text = path.read_text(encoding="utf-8")
        unresolved.extend(_TOKEN_RE.findall(text))
    return sorted(set(unresolved))


def main() -> int:
    os.environ.setdefault("GRATEFUL_DATA_TIER", "archival")
    variables = _write_counts()

    out_dir = ROOT / "output" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "manuscript_variables.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(variables, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(out_path)

    template_root = find_template_root(ROOT)
    if str(template_root) not in sys.path:
        sys.path.insert(0, str(template_root))

    from infrastructure.rendering.manuscript_injection import (
        write_resolved_manuscript_tree,
    )

    resolved_dir = write_resolved_manuscript_tree(ROOT, variables)
    leftover = _unresolved_tokens(resolved_dir)
    if leftover:
        raise SystemExit(
            f"unresolved manuscript tokens after injection: {', '.join(leftover)}"
        )
    print(resolved_dir)
    return 0
