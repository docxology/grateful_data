#!/usr/bin/env python3
"""Compare a refresh candidate against committed archival data.

This script never overwrites ``data/archival/``. Optional online refreshes are
written under ``output/refresh/archival_candidate/`` before comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.ingest.build import build_archival_compendium  # noqa: E402
from src.ingest.geo_enrich import enrich_venue_geo  # noqa: E402
from src.ingest.write_archival_seed import compendium_to_seed_files  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _json_count(path: Path) -> int | None:
    try:
        data = _load_json(path)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        return len(data)
    return None


def compare_archival_dirs(baseline_dir: Path, candidate_dir: Path) -> dict[str, object]:
    """Return deterministic JSON-file differences between two archival dirs."""

    baseline_files = {path.name: path for path in sorted(baseline_dir.glob("*.json"))}
    candidate_files = {path.name: path for path in sorted(candidate_dir.glob("*.json"))}
    added = sorted(set(candidate_files) - set(baseline_files))
    removed = sorted(set(baseline_files) - set(candidate_files))
    common = sorted(set(baseline_files) & set(candidate_files))
    changed: list[dict[str, object]] = []
    unchanged: list[str] = []
    for name in common:
        base = baseline_files[name]
        candidate = candidate_files[name]
        base_hash = _sha256(base)
        candidate_hash = _sha256(candidate)
        if base_hash == candidate_hash:
            unchanged.append(name)
            continue
        changed.append(
            {
                "file": name,
                "baseline_sha256": base_hash,
                "candidate_sha256": candidate_hash,
                "baseline_count": _json_count(base),
                "candidate_count": _json_count(candidate),
            }
        )
    return {
        "schema": "grateful-data-archival-refresh-diff-v1",
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "added_files": added,
        "removed_files": removed,
        "changed_files": changed,
        "unchanged_files": unchanged,
        "changes_detected": bool(added or removed or changed),
        "protected_baseline": "data/archival is read-only for this operation",
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Archival Refresh Diff",
        "",
        f"- Baseline: `{payload['baseline_dir']}`",
        f"- Candidate: `{payload['candidate_dir']}`",
        f"- Changes detected: `{payload['changes_detected']}`",
        f"- Added files: {len(payload['added_files'])}",
        f"- Removed files: {len(payload['removed_files'])}",
        f"- Changed files: {len(payload['changed_files'])}",
        "",
        "## Changed JSON Files",
        "",
    ]
    changed = payload["changed_files"]
    if not changed:
        lines.append("No JSON content changes detected.")
    else:
        lines.extend(
            [
                "| File | Baseline count | Candidate count |",
                "| --- | ---: | ---: |",
            ]
        )
        for row in changed:  # type: ignore[assignment]
            lines.append(
                f"| {row['file']} | {row['baseline_count']} | {row['candidate_count']} |"
            )
    lines.append("")
    lines.append("This report is advisory and does not mutate committed archival data.")
    lines.append("")
    return "\n".join(lines)


def _write_online_candidate(candidate_dir: Path, report_dir: Path) -> dict[str, object]:
    compendium, report = build_archival_compendium(online=True)
    geo_rows = enrich_venue_geo(compendium)
    compendium_to_seed_files(compendium, candidate_dir, geo_rows)
    payload = {
        "built_at": report.built_at,
        "sources_used": report.sources_used,
        "skipped": report.skipped,
        "entity_counts": report.entity_counts,
        "ingest_stats": report.ingest_stats,
        "coverage_pct": report.coverage_pct,
        "corpus_scope": report.corpus_scope,
        "candidate_dir": str(candidate_dir),
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    with (report_dir / "refresh_build_report.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=ROOT / "data" / "archival",
        help="Committed archival directory to read.",
    )
    parser.add_argument(
        "--candidate-dir",
        type=Path,
        default=None,
        help="Candidate archival-shaped directory. Defaults to baseline unless --online is used.",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Build a fresh candidate into output/refresh/archival_candidate before diffing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = ROOT / "output" / "refresh"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = args.candidate_dir or (
        out_dir / "archival_candidate" if args.online else args.baseline_dir
    )
    refresh_payload: dict[str, object] | None = None
    if args.online:
        refresh_payload = _write_online_candidate(candidate_dir, out_dir)
    payload = compare_archival_dirs(args.baseline_dir, candidate_dir)
    if refresh_payload:
        payload["refresh_build_report"] = refresh_payload
    json_path = out_dir / "archival_refresh_diff.json"
    markdown_path = out_dir / "archival_refresh_diff.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    markdown_path.write_text(render_markdown(payload), encoding="utf-8")
    print(json_path)
    print(markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
