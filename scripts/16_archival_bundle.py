#!/usr/bin/env python3
"""Package archival exports with manifest and optional tarball."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.export import export_all  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def main() -> None:
    archival_out = ROOT / "output" / "archival"
    raw_dir = ROOT / "output" / "data" / "raw"
    archival_out.mkdir(parents=True, exist_ok=True)

    comp = load_seed_compendium()
    export_all(comp, raw_dir)

    file_hashes: dict[str, str] = {}
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(ROOT).as_posix()
            file_hashes[rel] = _sha256(path)

    completeness = ROOT / "output" / "reports" / "completeness_report.json"
    figure_val = ROOT / "output" / "reports" / "figure_validation.json"
    fetch_manifest = ROOT / "output" / "data" / "fetch_manifest.json"
    build_report = archival_out / "build_report.json"

    manifest = {
        "tier": "archival",
        "git_head": _git_head(),
        "entity_counts": {
            "shows": len(comp.shows),
            "performances": len(comp.performances),
            "songs": len(comp.songs),
            "venues": len(comp.venues),
        },
        "file_hashes": file_hashes,
        "completeness_report": str(completeness) if completeness.exists() else None,
        "figure_validation": str(figure_val) if figure_val.exists() else None,
        "fetch_manifest": str(fetch_manifest) if fetch_manifest.exists() else None,
        "build_report": str(build_report) if build_report.exists() else None,
    }

    manifest_path = archival_out / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    tarball = archival_out / "grateful_data_archival.tar.gz"
    with tarfile.open(tarball, "w:gz") as tar:
        tar.add(raw_dir, arcname="raw")
        tar.add(manifest_path, arcname="manifest.json")
        if build_report.exists():
            tar.add(build_report, arcname="build_report.json")

    print(manifest_path)
    print(tarball)


if __name__ == "__main__":
    main()
