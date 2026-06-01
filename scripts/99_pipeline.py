#!/usr/bin/env python3
"""End-to-end pipeline for the grateful_data project."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

STAGES = (
    "00_fetch_sources.py",
    "01_build_compendium.py",
    "02_analyze.py",
    "03_category_theory.py",
    "13_audit_completeness.py",
    "19_first_principles_review.py",
    "15_export_raw.py",
    "23_export_provenance.py",
    "04_figures.py",
    "05_extended_figures.py",
    "06_mosaic.py",
    "08_more_figures.py",
    "10_alluvial.py",
    "18_export_figure_data.py",
    "07_dashboard.py",
    "24_external_manifests.py",
    "25_generate_explorer.py",
    "14_validate_figures.py",
    "26_peer_review_dossier.py",
    "27_promotion_readiness.py",
)

ARCHIVAL_EXTRA = ("16_archival_bundle.py", "17_reconcile_sources.py")
MANUSCRIPT_COUNTS = "z_generate_manuscript_variables.py"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tier",
        choices=("seed", "archival"),
        default="seed",
        help="data tier: seed (CI demonstrator) or archival (full gdshowsdb snapshot)",
    )
    parser.add_argument(
        "--fetch-archival",
        action="store_true",
        help="when tier=archival, run 00_fetch_sources --online --write-archival first",
    )
    args, _ = parser.parse_known_args()

    os.environ["GRATEFUL_DATA_TIER"] = args.tier

    if args.fetch_archival and args.tier == "archival":
        fetch = SCRIPTS / "00_fetch_sources.py"
        sys.argv = [str(fetch), "--online", "--write-archival"]
        runpy.run_path(str(fetch), run_name="__main__")

    stages = list(STAGES)
    if args.tier == "archival":
        # Insert bundle after export
        idx = stages.index("15_export_raw.py") + 1
        stages[idx:idx] = list(ARCHIVAL_EXTRA)

    for name in stages:
        if name == "00_fetch_sources.py" and not args.fetch_archival:
            continue
        path = SCRIPTS / name
        print(f"\n=== {name} ===")
        sys.argv = [str(path)]
        try:
            runpy.run_path(str(path), run_name="__main__")
        except SystemExit as exc:
            code = (
                exc.code
                if isinstance(exc.code, int)
                else (0 if exc.code is None else 1)
            )
            if code != 0:
                raise SystemExit(
                    f"pipeline aborted: stage {name} exited {code}"
                ) from exc

    counts_path = SCRIPTS / MANUSCRIPT_COUNTS
    print(f"\n=== {MANUSCRIPT_COUNTS} ===")
    sys.argv = [str(counts_path)]
    runpy.run_path(str(counts_path), run_name="__main__")


if __name__ == "__main__":
    main()
