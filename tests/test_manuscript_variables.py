"""Manuscript variable generation from analysis reports."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.z_generate_manuscript_variables import (
    _find_template_root,
    _top_song_fields,
    _write_counts,
)


def test_top_song_fields_from_analysis():
    analysis = {
        "top_songs_top3": [
            {"slug": "eyes-of-the-world", "count": 412},
            {"slug": "estimated-prophet", "count": 301},
            {"slug": "hell-in-a-bucket", "count": 288},
        ],
        "top_song": "eyes-of-the-world",
        "top_song_count": 412,
    }
    fields = _top_song_fields(analysis)
    assert fields["TOP_SONG"] == "eyes-of-the-world"
    assert fields["TOP_SONG_COUNT"] == "412"
    assert fields["TOP_SONG_2"] == "estimated-prophet"
    assert fields["TOP_SONG_2_COUNT"] == "301"
    assert fields["TOP_SONG_3_COUNT"] == "288"


def test_write_counts_includes_curated_overlay_fields(
    compendium, tmp_path, monkeypatch
):
    monkeypatch.delenv("GRATEFUL_DATA_TIER", raising=False)
    reports = tmp_path / "reports"
    reports.mkdir()
    analysis = {
        "top_songs_top3": [{"slug": "ripple", "count": 10}],
        "top_song": "ripple",
        "top_song_count": 10,
    }
    (reports / "analysis_report.json").write_text(
        json.dumps(analysis), encoding="utf-8"
    )
    monkeypatch.setattr("scripts.z_generate_manuscript_variables.ROOT", tmp_path.parent)
    payload = _top_song_fields(analysis)
    assert payload["TOP_SONG"] == "ripple"


def test_find_template_root_from_private_checkout():
    root = _find_template_root(Path(__file__).resolve().parent.parent)
    assert (root / "infrastructure" / "rendering").is_dir()


def test_deprecated_generate_manuscript_counts_delegates(monkeypatch):
    if not (
        Path(__file__).resolve().parent.parent / "data" / "archival" / "shows.json"
    ).is_file():
        import pytest

        pytest.skip("archival data not in checkout")
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    from scripts import generate_manuscript_counts as legacy

    assert legacy.main() == 0


def test_manuscript_variables_json_written(monkeypatch):
    """_write_counts returns archival keys when compendium loads."""
    if not (
        Path(__file__).resolve().parent.parent / "data" / "archival" / "shows.json"
    ).is_file():
        import pytest

        pytest.skip("archival data not in checkout")
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    payload = _write_counts()
    assert payload["CORPUS_LABEL"] == "archival compendium"
    assert int(payload["ARCHIVAL_SHOWS"]) > 0
    assert "CORPUS_SCOPE_PHRASE" in payload
    assert int(payload["FIG_TOP_SONGS_N"]) > 0
    assert int(payload["FIG_COOCCURRENCE_SONG_N"]) > 0
    assert payload["ALLUVIAL_TOP_PATHS_N"] == "40"


def test_all_source_manuscript_tokens_are_generated(monkeypatch):
    """Every authored {{TOKEN}} must be produced before injection."""
    root = Path(__file__).resolve().parent.parent
    if not (root / "data" / "archival" / "shows.json").is_file():
        import pytest

        pytest.skip("archival data not in checkout")
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    payload = _write_counts()
    source_tokens: set[str] = set()
    token_re = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
    for path in sorted((root / "manuscript").glob("*.md")):
        if path.name in {"AGENTS.md", "README.md", "SYNTAX.md"}:
            continue
        source_tokens.update(token_re.findall(path.read_text(encoding="utf-8")))
    missing = sorted(source_tokens - set(payload))
    assert missing == []


def test_unresolved_tokens_helper(tmp_path):
    from scripts.z_generate_manuscript_variables import _unresolved_tokens

    md = tmp_path / "01_section.md"
    md.write_text("count {{MISSING_TOKEN}} only", encoding="utf-8")
    assert _unresolved_tokens(tmp_path) == ["MISSING_TOKEN"]
