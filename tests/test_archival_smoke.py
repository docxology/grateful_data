"""Structural smoke checks for the committed archival tier (no pinned counts)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.audit import audit_completeness
from src.seed import load_seed_compendium
from src.tier import ARCHIVAL_DIR

pytestmark = pytest.mark.skipif(
    not ARCHIVAL_DIR.is_dir() or not (ARCHIVAL_DIR / "shows.json").exists(),
    reason="data/archival snapshot not present",
)


@pytest.fixture
def archival_compendium():
    """Per-test archival compendium with tier env restored."""

    if not ARCHIVAL_DIR.is_dir() or not (ARCHIVAL_DIR / "shows.json").exists():
        pytest.skip("data/archival snapshot not present")
    prev = os.environ.get("GRATEFUL_DATA_TIER")
    os.environ["GRATEFUL_DATA_TIER"] = "archival"
    try:
        yield load_seed_compendium()
    finally:
        if prev is None:
            os.environ.pop("GRATEFUL_DATA_TIER", None)
        else:
            os.environ["GRATEFUL_DATA_TIER"] = prev


def test_archival_scale_and_audit(archival_compendium) -> None:
    comp = archival_compendium
    assert len(comp.shows) >= 2000
    assert len(comp.performances) >= 30000
    report = audit_completeness(comp)
    assert report.dangling_total == 0
    assert report.geo_coverage_pct == 100.0
    if (ARCHIVAL_DIR / "performances.json").exists():
        assert report.n_segue_markers > 10_000


def test_archival_venue_geo_complete(archival_compendium) -> None:
    geo_path = ARCHIVAL_DIR / "venue_geo.json"
    assert geo_path.is_file()
    rows = json.loads(geo_path.read_text(encoding="utf-8"))
    assert len(rows) == len(archival_compendium.venues)


def test_archival_build_report_present() -> None:
    path = (
        Path(__file__).resolve().parent.parent
        / "output"
        / "archival"
        / "build_report.json"
    )
    if not path.exists():
        pytest.skip("run 00_fetch_sources --write-archival first")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["entity_counts"]["shows"] >= 2000
