"""Tests for publication guardrails and large-item scaffolds."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from src.external_manifests import ExternalPointer, write_external_manifests
from src.provenance import lookup_provenance, provenance_records, write_provenance
from src.reporting.explorer import write_explorer
from src.reporting.peer_review import write_peer_review_dossier
from src.reporting.release_prep import build_steps
from src.viz.figures import DASHBOARD_FIGURES, FIGURE_SPECS

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    path = ROOT / "scripts" / name
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_sidecar_exports_and_lookup(tmp_path, compendium):
    records = provenance_records(compendium)
    assert records
    matches = lookup_provenance(records, "songs", "ripple")
    assert matches
    assert "alex-allan-whitegum" in matches[0].source_keys

    csv_path, json_path = write_provenance(compendium, tmp_path)
    assert csv_path.read_text(encoding="utf-8").startswith(
        "entity_type,key,source_keys"
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["record_count"] == len(records)
    assert (tmp_path / "songs.csv").exists()


def test_external_manifests_are_pointer_only(tmp_path, compendium):
    audio_path, lyric_path, summary_path = write_external_manifests(compendium, tmp_path)
    assert audio_path.exists()
    assert lyric_path.exists()
    assert (tmp_path / "pipeline_contract.json").exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "Pointer metadata only" in summary["policy"]
    assert "pipeline_contract" in summary["files"]

    with pytest.raises(ValueError):
        ExternalPointer(
            kind="lyrics",
            key="ripple",
            url="https://example.com/ripple",
            metadata={"lyric_text": "forbidden"},
        )
    with pytest.raises(ValueError):
        ExternalPointer(
            kind="audio",
            key="sample",
            url="file:///tmp/audio.flac",
            metadata={"policy": "not-a-pointer"},
        )


def test_static_explorer_and_peer_review_dossier(tmp_path, compendium):
    html_path, data_path = write_explorer(compendium, tmp_path / "explorer")
    html = html_path.read_text(encoding="utf-8")
    assert "data-search" in html
    assert "download-filtered" in html
    assert "URLSearchParams" in html
    assert "figures" in html
    assert "related_figures" in html
    assert "data-sort" not in html  # v3 uses explicit data-key/data-col headers.
    assert "claim_evidence" in html
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "grateful-data-static-explorer-v3"
    assert payload["summary"]["claim_rows"] >= 10
    assert payload["figures"]
    assert payload["songs"][0]["related_figures"]
    assert payload["claim_evidence"]

    reports = tmp_path / "reports"
    figures = tmp_path / "figures"
    reports.mkdir()
    figures.mkdir()
    dossier_json, dossier_md = write_peer_review_dossier(
        compendium, reports, reports_dir=reports, figures_dir=figures
    )
    dossier = json.loads(dossier_json.read_text(encoding="utf-8"))
    assert dossier["claim_count"] == payload["summary"]["claim_rows"]
    assert "Peer-Review Dossier" in dossier_md.read_text(encoding="utf-8")


def _write_publication_fixture(root: Path) -> None:
    output = root / "output"
    (output / "pdf").mkdir(parents=True)
    (output / "web").mkdir(parents=True)
    (output / "reports").mkdir(parents=True)
    (output / "data" / "figures").mkdir(parents=True)
    (output / "data" / "provenance").mkdir(parents=True)
    (output / "data" / "external").mkdir(parents=True)
    (output / "explorer").mkdir(parents=True)
    (output / "manuscript").mkdir(parents=True)

    (output / "pdf" / "grateful_data_combined.pdf").write_bytes(b"%PDF-1.4\n")
    (output / "pdf" / "_combined_manuscript.log").write_text(
        "clean render\n", encoding="utf-8"
    )
    (output / "web" / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    (output / "explorer" / "index.html").write_text("<html>ok</html>", encoding="utf-8")
    (output / "manuscript" / "body.md").write_text("resolved", encoding="utf-8")
    (output / "reports" / "figure_validation.json").write_text(
        json.dumps({"all_ok": True, "n_ok": 1, "n_figures": 1}), encoding="utf-8"
    )
    (output / "reports" / "completeness_report.json").write_text(
        json.dumps({"dangling_total": 0}), encoding="utf-8"
    )
    (output / "reports" / "first_principles_review.json").write_text(
        json.dumps({"rows": []}), encoding="utf-8"
    )
    (output / "reports" / "peer_review_dossier.json").write_text(
        json.dumps({"claims": []}), encoding="utf-8"
    )
    (output / "data" / "provenance" / "provenance.json").write_text(
        json.dumps({"records": []}), encoding="utf-8"
    )
    (output / "data" / "external" / "external_manifest_summary.json").write_text(
        json.dumps({"policy": "pointer-only"}), encoding="utf-8"
    )
    (output / "data" / "external" / "pipeline_contract.json").write_text(
        json.dumps({"schema": "contract"}), encoding="utf-8"
    )

    data_dir = output / "data" / "figures"
    rows = []
    dashboard_links = []
    for spec in FIGURE_SPECS:
        if spec.dataset is None:
            continue
        stem = spec.filename.removesuffix(".png")
        csv_name = f"{stem}.csv"
        json_name = f"{stem}.json"
        (data_dir / csv_name).write_text("col\n", encoding="utf-8")
        (data_dir / json_name).write_text("{}", encoding="utf-8")
        rows.append(
            {
                "figure": spec.filename,
                "title": spec.display_title,
                "display_title": spec.display_title,
                "alt_text": spec.alt_text,
                "caption_hint": spec.caption_hint,
                "data_source": spec.data_source,
                "statistic": spec.statistic,
                "exclusion_rule": spec.exclusion_rule,
                "claim_class": spec.claim_class,
                "csv": csv_name,
                "json": json_name,
                "n_rows": 1,
                "columns": ["col"],
                "metadata": {},
            }
        )
        if spec.filename in DASHBOARD_FIGURES:
            dashboard_links.extend(
                [
                    f'<a href="data/figures/{csv_name}">CSV</a>',
                    f'<a href="data/figures/{json_name}">JSON</a>',
                ]
            )
    (data_dir / "index.json").write_text(
        json.dumps({"n_datasets": len(rows), "datasets": rows}), encoding="utf-8"
    )
    (output / "dashboard.html").write_text(
        "<html>" + "\n".join(dashboard_links) + "</html>", encoding="utf-8"
    )


def test_publication_validator_passes_and_catches_regressions(tmp_path):
    validator = _load_script("20_validate_publication_outputs.py")
    _write_publication_fixture(tmp_path)
    report = validator.validate_publication_outputs(tmp_path)
    assert report["all_ok"] is True

    (tmp_path / "output" / "web" / "index.html").write_text(
        "bad {{TOKEN}} [@missing]", encoding="utf-8"
    )
    broken = validator.validate_publication_outputs(tmp_path)
    failed = {row["name"] for row in broken["checks"] if not row["ok"]}
    assert "no_unresolved_tokens" in failed
    assert "no_raw_markdown_citations_in_rendered_outputs" in failed


def test_release_prep_dry_run_ordering():
    steps = build_steps(
        tier="archival",
        template_root=Path("/tmp/template"),
        skip_tests=False,
        skip_pipeline=False,
        skip_render=False,
        skip_validator=False,
    )
    assert [step.name for step in steps] == [
        "tests",
        "archival_pipeline",
        "template_render",
        "publication_validator",
    ]


def test_archival_refresh_diff_detects_json_changes(tmp_path):
    refresh = _load_script("22_archival_refresh_diff.py")
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    baseline.mkdir()
    candidate.mkdir()
    (baseline / "shows.json").write_text('[{"slug":"a"}]\n', encoding="utf-8")
    (candidate / "shows.json").write_text(
        '[{"slug":"a"},{"slug":"b"}]\n', encoding="utf-8"
    )
    (candidate / "songs.json").write_text("[]\n", encoding="utf-8")
    report = refresh.compare_archival_dirs(baseline, candidate)
    assert report["changes_detected"] is True
    assert report["added_files"] == ["songs.json"]
    assert report["changed_files"][0]["candidate_count"] == 2
