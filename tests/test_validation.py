"""Tests for seed JSON shape validation."""

from __future__ import annotations

import json
import shutil

import pytest

from src.validation import SeedValidationError, assert_valid, validate_seed

SEED_DIR = (
    __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "seed"
)


def test_validate_seed_passes_on_bundled_fixture():
    violations = validate_seed(SEED_DIR)
    assert violations == ()


def test_assert_valid_passes_on_bundled_fixture():
    assert_valid(SEED_DIR)


def test_validate_seed_reports_missing_file(tmp_path):
    shutil.copytree(SEED_DIR, tmp_path / "seed")
    (tmp_path / "seed" / "shows.json").unlink()
    violations = validate_seed(tmp_path / "seed")
    assert any("shows.json: missing" in v for v in violations)


def test_validate_seed_reports_unexpected_key(tmp_path):
    shutil.copytree(SEED_DIR, tmp_path / "seed")
    shows_path = tmp_path / "seed" / "shows.json"
    shows = json.loads(shows_path.read_text(encoding="utf-8"))
    shows[0]["extra_field"] = True
    shows_path.write_text(json.dumps(shows), encoding="utf-8")
    violations = validate_seed(tmp_path / "seed")
    assert any("unexpected key 'extra_field'" in v for v in violations)


def test_assert_valid_raises_on_violation(tmp_path):
    shutil.copytree(SEED_DIR, tmp_path / "seed")
    shows_path = tmp_path / "seed" / "shows.json"
    shows = json.loads(shows_path.read_text(encoding="utf-8"))
    del shows[0]["date"]
    shows_path.write_text(json.dumps(shows), encoding="utf-8")
    with pytest.raises(SeedValidationError) as exc:
        assert_valid(tmp_path / "seed")
    assert any("missing required 'date'" in v for v in exc.value.violations)
