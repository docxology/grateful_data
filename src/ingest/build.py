"""Orchestrate archival compendium build from vendor + curated layers."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..audit import FULL_CORPUS_SHOW_ESTIMATE
from ..integration.reconcile import Compendium
from .gdshowsdb_yaml import load_gdshowsdb_vendor
from .geo_enrich import enrich_venue_geo
from .merge_sources import MergeInputs, merge_archival
from .write_archival_seed import compendium_to_seed_files

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SEED_DIR = PROJECT_ROOT / "data" / "seed"
ARCHIVAL_DIR = PROJECT_ROOT / "data" / "archival"
VENDOR_DIR = PROJECT_ROOT / "data" / "vendor" / "gdshowsdb"
GDSHOWSDB_REPO = "https://github.com/jefmsmit/gdshowsdb.git"


@dataclass
class BuildReport:
    built_at: str
    sources_used: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    entity_counts: dict[str, int] = field(default_factory=dict)
    ingest_stats: dict[str, int] = field(default_factory=dict)
    corpus_scope: str = ""
    coverage_pct: float = 0.0


def ensure_gdshowsdb_vendor(*, online: bool) -> Path:
    """Return vendor path, cloning gdshowsdb when ``online`` and missing."""
    if VENDOR_DIR.is_dir() and (VENDOR_DIR / "data" / "gdshowsdb").is_dir():
        return VENDOR_DIR
    if not online:
        raise FileNotFoundError(
            f"gdshowsdb vendor not found at {VENDOR_DIR}; run with --online to clone"
        )
    VENDOR_DIR.parent.mkdir(parents=True, exist_ok=True)
    if VENDOR_DIR.exists():
        shutil.rmtree(VENDOR_DIR)
    subprocess.run(
        ["git", "clone", "--depth", "1", GDSHOWSDB_REPO, str(VENDOR_DIR)],
        check=True,
        capture_output=True,
        text=True,
    )
    return VENDOR_DIR


def build_archival_compendium(
    *,
    online: bool = False,
    ia_max_rows: int = 0,
    setlistfm_max_pages: int = 0,
    skip_cmu: bool = False,
    skip_whitegum: bool = False,
    skip_dead_net: bool = False,
    skip_wikipedia: bool = False,
) -> tuple[Compendium, BuildReport]:
    """Load gdshowsdb YAML + curated seed layers into one compendium."""
    vendor = ensure_gdshowsdb_vendor(online=online)
    dump = load_gdshowsdb_vendor(vendor)
    comp, merge_report = merge_archival(
        MergeInputs(
            gdshows_dump=dump,
            curated_seed_dir=SEED_DIR,
            online=online,
            ia_max_rows=ia_max_rows,
            setlistfm_max_pages=setlistfm_max_pages,
            skip_cmu=skip_cmu,
            skip_whitegum=skip_whitegum,
            skip_dead_net=skip_dead_net,
            skip_wikipedia=skip_wikipedia,
        )
    )
    n_shows = len(comp.shows)
    pct = (
        100.0 * n_shows / FULL_CORPUS_SHOW_ESTIMATE
        if FULL_CORPUS_SHOW_ESTIMATE
        else 0.0
    )
    report = BuildReport(
        built_at=datetime.now(timezone.utc).isoformat(),
        sources_used=merge_report.sources_used,
        skipped=merge_report.skipped,
        entity_counts=merge_report.entity_counts,
        ingest_stats=merge_report.ingest_stats,
        coverage_pct=pct,
        corpus_scope=(
            f"archival tier: {n_shows} shows (~{pct:.1f}% of "
            f"~{FULL_CORPUS_SHOW_ESTIMATE}-show estimate) from gdshowsdb + curated layers"
        ),
    )
    return comp, report


def write_archival_snapshot(
    comp: Compendium,
    report: BuildReport,
    *,
    out_dir: Path | None = None,
) -> Path:
    """Write ``data/archival/`` JSON + build report."""
    target = Path(out_dir) if out_dir else ARCHIVAL_DIR
    geo_rows = enrich_venue_geo(comp, seed_dir=SEED_DIR)
    compendium_to_seed_files(comp, target, geo_rows)
    out_reports = PROJECT_ROOT / "output" / "archival"
    out_reports.mkdir(parents=True, exist_ok=True)
    build_path = out_reports / "build_report.json"
    with build_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "built_at": report.built_at,
                "sources_used": report.sources_used,
                "skipped": report.skipped,
                "entity_counts": report.entity_counts,
                "ingest_stats": report.ingest_stats,
                "corpus_scope": report.corpus_scope,
                "coverage_pct": report.coverage_pct,
                "archival_dir": str(target),
                "curated_overlays": {
                    "reviews": "data/seed/reviews.json — curated exemplar; archival online adds maximinus corpus",
                    "citations": "data/seed/citations.json — curated exemplar; archival adds bibliography_combined (MD + references.bib)",
                    "lyric_pointers": "data/seed/lyric_pointers.json — pointer metadata; archival online adds CMU lyrics index, curated theme overlay, dead.net gap-fill",
                    "personnel": "data/seed/personnel.json — authoritative intervals when present",
                },
            },
            fh,
            indent=2,
        )
        fh.write("\n")
    return target
