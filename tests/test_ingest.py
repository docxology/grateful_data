"""Tests for archival ingest (fixture-based, no mocks)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ingest.gdshowsdb_yaml import load_gdshowsdb_vendor
from src.ingest.merge_sources import MergeInputs, merge_archival
from src.ingest.write_archival_seed import compendium_to_seed_files
from src.seed import load_seed_compendium
from src.validation import assert_valid

FIXTURE_VENDOR = (
    Path(__file__).resolve().parent / "fixtures" / "ingest" / "gdshowsdb_mini"
)


@pytest.fixture(scope="module")
def mini_vendor(tmp_path_factory):
    """Two-show gdshowsdb YAML tree for ingest tests."""
    root = FIXTURE_VENDOR
    if not root.is_dir():
        pytest.skip("ingest fixture vendor missing")
    return root


def test_load_gdshowsdb_yaml_mini(mini_vendor):
    dump = load_gdshowsdb_vendor(mini_vendor)
    assert len(dump["shows"]) >= 2
    assert len(dump["performances"]) >= 2
    assert len(dump["venues"]) >= 1


def test_merge_archival_offline_mini(mini_vendor):
    dump = load_gdshowsdb_vendor(mini_vendor)
    comp, report = merge_archival(
        MergeInputs(
            gdshows_dump=dump,
            curated_seed_dir=Path(__file__).resolve().parents[1] / "data" / "seed",
            online=False,
        )
    )
    assert report.entity_counts["shows"] >= 2
    assert len(comp.performances) >= 2
    assert len(comp.citations) >= 1


def test_write_archival_round_trip(tmp_path, mini_vendor):
    dump = load_gdshowsdb_vendor(mini_vendor)
    comp, _ = merge_archival(
        MergeInputs(
            gdshows_dump=dump,
            curated_seed_dir=Path(__file__).resolve().parents[1] / "data" / "seed",
            online=False,
        )
    )
    from src.ingest.geo_enrich import enrich_venue_geo

    geo = enrich_venue_geo(
        comp, seed_dir=Path(__file__).resolve().parents[1] / "data" / "seed"
    )
    out = tmp_path / "archival"
    compendium_to_seed_files(comp, out, geo)
    assert_valid(out)
    reloaded = load_seed_compendium(out)
    assert len(reloaded.shows) == len(comp.shows)
    assert len(reloaded.performances) == len(comp.performances)
    src_segues = sum(1 for p in comp.performances if p.segue_into)
    dst_segues = sum(1 for p in reloaded.performances if p.segue_into)
    assert dst_segues == src_segues
