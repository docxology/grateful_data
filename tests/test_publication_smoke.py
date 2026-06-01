"""Publication smoke: resolved manuscript tokens and figure registry."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.viz.figures import EXPECTED_FILENAMES, render_group  # noqa: E402

_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


def _find_template_root(start: Path) -> Path:
    env = os.environ.get("TEMPLATE_REPO_ROOT", "").strip()
    if env:
        root = Path(env)
        if (root / "infrastructure" / "rendering").is_dir():
            return root
    for candidate in (start, *start.parents):
        if (candidate / "infrastructure" / "rendering").is_dir():
            return candidate
    pytest.skip("template repo root not found for manuscript injection")


def test_z_generate_leaves_no_unresolved_tokens(tmp_path, monkeypatch):
    """Hydrated output/manuscript must have zero {{TOKENS}}."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "00_test.md").write_text(
        "Shows: {{ARCHIVAL_SHOWS}} tier {{CORPUS_LABEL}}.", encoding="utf-8"
    )
    (tmp_path / "output" / "reports").mkdir(parents=True)
    (tmp_path / "data" / "archival").mkdir(parents=True)

    # Minimal archival JSON so load_seed_compendium works in isolation is heavy;
    # invoke generator on real project when run from grateful_data checkout.
    if not (ROOT / "data" / "archival" / "shows.json").is_file():
        pytest.skip("archival data not present in checkout")

    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "z_generate_manuscript_variables.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    resolved = ROOT / "output" / "manuscript"
    assert resolved.is_dir()
    leftover: list[str] = []
    for path in sorted(resolved.glob("*.md")):
        if path.name in {"AGENTS.md", "README.md", "SYNTAX.md"}:
            continue
        leftover.extend(_TOKEN_RE.findall(path.read_text(encoding="utf-8")))
    assert leftover == [], f"unresolved tokens: {sorted(set(leftover))}"

    vars_path = ROOT / "output" / "data" / "manuscript_variables.json"
    assert vars_path.is_file()
    payload = json.loads(vars_path.read_text(encoding="utf-8"))
    assert payload.get("CORPUS_LABEL") == "archival compendium"
    assert int(payload.get("ARCHIVAL_SHOWS", "0")) > 0


def test_core_figures_render_on_archival_compendium(tmp_path, compendium):
    paths = render_group(compendium, tmp_path, "core")
    assert len(paths) == 5
    for path in paths:
        assert path.stat().st_size > 500


def test_expected_filenames_count():
    assert len(EXPECTED_FILENAMES) == 36


def test_results_figure_captions_are_evidence_structured():
    text = (ROOT / "manuscript" / "04_results.md").read_text(encoding="utf-8")
    captions = re.findall(
        r"\\includegraphics\[[^\]]*\]\{[^}]+\}\n\\caption\{(.*?)\}\n\\label\{([^}]+)\}",
        text,
        flags=re.S,
    )
    assert len(captions) == len(EXPECTED_FILENAMES)
    required = ("Data source:", "Statistic:", "Exclusion rule:", "Claim class:")
    missing = {
        label: [field for field in required if field not in caption]
        for caption, label in captions
    }
    missing = {label: fields for label, fields in missing.items() if fields}
    assert missing == {}
