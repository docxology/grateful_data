"""Tests for the first-principles claim/evidence ledger."""

from __future__ import annotations

import json

from src.analysis import first_principles


def test_claim_evidence_rows_are_complete_and_classified(compendium):
    rows = first_principles.claim_evidence_rows(compendium)
    assert len(rows) >= 10
    seen_classes = {row.claim_class for row in rows}
    assert {"Descriptive", "Structural", "Exploratory", "Boundary"} <= seen_classes
    for row in rows:
        payload = row.to_dict()
        assert set(payload) == {
            "claim_area",
            "claim_class",
            "irreducible_input",
            "hard_constraint",
            "soft_constraint",
            "assumption",
            "validation_artifact",
            "artifact_family",
            "interpretation_limit",
            "figure_or_report",
            "manuscript_section",
            "figure_filename",
            "report_key",
            "test_file",
            "claim_status",
        }
        assert all(str(value).strip() for value in payload.values())


def test_claim_evidence_matrix_matches_rows(compendium):
    rows = first_principles.claim_evidence_rows(compendium)
    matrix, claim_classes, artifact_families = first_principles.claim_evidence_matrix(
        compendium
    )
    assert claim_classes == first_principles.CLAIM_CLASSES
    assert artifact_families == first_principles.ARTIFACT_FAMILIES
    assert sum(sum(row) for row in matrix) == len(rows)


def test_write_review_outputs_json_and_csv(tmp_path, compendium):
    json_path, csv_path = first_principles.write_review(compendium, tmp_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["n_claim_areas"] == len(
        first_principles.claim_evidence_rows(compendium)
    )
    assert payload["n_hard_constraints"] >= payload["n_claim_classes"]
    text = csv_path.read_text(encoding="utf-8")
    assert "claim_area,claim_class,irreducible_input" in text
    assert "Repertoire ranking" in text
