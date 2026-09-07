#!/usr/bin/env python3
"""Write a promotion-readiness report without changing lifecycle folders."""

from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()


def _exists(path: Path) -> bool:
    return path.is_file() or path.is_dir()


def _promotion_command(root: Path) -> str:
    """Portable lifecycle move: sibling ``active/`` beside the ``projects/`` ancestor."""
    for ancestor in root.parents:
        if ancestor.name == "projects":
            return f"mv {root} {ancestor / 'active' / root.name}"
    return f"mv {root} {root.parent / 'active' / root.name}"


def main() -> int:
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    cwd_text = str(ROOT)
    checks = [
        {
            "name": "working_lifecycle",
            "ok": "/working/" in cwd_text,
            "detail": "Project remains in working/; this script does not promote it.",
        },
        {
            "name": "test_contract_present",
            "ok": _exists(ROOT / "tests"),
            "detail": "Tests directory exists for standalone 90% coverage gate.",
        },
        {
            "name": "pipeline_present",
            "ok": _exists(ROOT / "scripts" / "99_pipeline.py"),
            "detail": "Standalone analysis pipeline is available.",
        },
        {
            "name": "publication_validator_present",
            "ok": _exists(ROOT / "scripts" / "20_validate_publication_outputs.py"),
            "detail": "Publication validator is available.",
        },
        {
            "name": "release_prep_present",
            "ok": _exists(ROOT / "scripts" / "21_release_prep.py"),
            "detail": "Release-prep orchestrator is available.",
        },
        {
            "name": "latest_validation_report",
            "ok": _exists(ROOT / "output" / "reports" / "publication_validation.json"),
            "detail": "Latest publication validation report exists.",
        },
    ]
    payload = {
        "schema": "grateful-data-promotion-readiness-v1",
        "project_root": cwd_text,
        "does_not_promote": True,
        "ready_to_request_promotion": all(check["ok"] for check in checks),
        "checks": checks,
        "promotion_command_if_explicitly_requested": _promotion_command(ROOT),
        "required_pre_promotion_gates": [
            "uv run pytest tests/ --cov=src --cov-fail-under=90",
            "GRATEFUL_DATA_TIER=archival uv run python scripts/99_pipeline.py --tier archival",
            "uv run python scripts/20_validate_publication_outputs.py --strict",
        ],
    }
    path = out_dir / "promotion_readiness.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
