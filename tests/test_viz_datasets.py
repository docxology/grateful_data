"""Figure dataset export tests."""

from __future__ import annotations

import json

from src.viz import datasets
from src.viz.figures import FIGURE_SPECS
from src.analysis.markers import SEGMENT_MARKERS


def test_figure_dataset_writes_deterministic_csv_and_json(tmp_path):
    dataset = datasets.FigureDataset(
        figure="example.png",
        title="Example",
        columns=("name", "value"),
        rows=(("a", 2), ("b", 3)),
        metadata={"z": 1, "a": "first"},
    )
    csv_path, json_path = dataset.write_pair(tmp_path)
    assert csv_path.read_text(encoding="utf-8") == "name,value\na,2\nb,3\n"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["figure"] == "example.png"
    assert payload["metadata"] == {"a": "first", "z": 1}


def test_every_registered_panel_has_dataset_exporter():
    for spec in FIGURE_SPECS:
        assert spec.dataset is not None or spec.dataset_reason


def test_all_registered_dataset_exporters_build_real_tables(compendium):
    for spec in FIGURE_SPECS:
        assert spec.dataset is not None
        dataset = spec.dataset(compendium)
        assert dataset.figure == spec.filename
        assert dataset.title
        assert dataset.columns
        assert all(len(row) == len(dataset.columns) for row in dataset.rows)


def test_export_figure_datasets_writes_index_and_pairs(tmp_path, compendium):
    index_path = datasets.export_figure_datasets(compendium, FIGURE_SPECS, tmp_path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert payload["n_datasets"] == len(FIGURE_SPECS)
    assert (tmp_path / "top_songs.csv").is_file()
    assert (tmp_path / "top_songs.json").is_file()
    assert (tmp_path / "performance_distribution.csv").is_file()
    assert (tmp_path / "performance_distribution.json").is_file()
    assert (tmp_path / "repertoire_embedding.csv").is_file()
    assert (tmp_path / "era_repertoire_heatmap.json").is_file()
    assert (tmp_path / "claim_evidence_matrix.csv").is_file()
    assert (tmp_path / "transition_sensitivity.csv").is_file()
    assert (tmp_path / "repertoire_topn_sensitivity.json").is_file()
    assert (tmp_path / "venue_identity_review.csv").is_file()
    first = payload["datasets"][0]
    assert "data_source" in first
    assert "statistic" in first
    assert "exclusion_rule" in first
    assert "claim_class" in first


def test_transition_stationary_and_centrality_exports_exclude_generic_segments(compendium):
    for exporter in (
        datasets.transition_matrix,
        datasets.stationary_top20,
        datasets.centrality_top20,
    ):
        dataset = exporter(compendium)
        joined = "\n".join(",".join(str(cell) for cell in row) for row in dataset.rows)
        for marker in SEGMENT_MARKERS:
            assert marker not in joined
