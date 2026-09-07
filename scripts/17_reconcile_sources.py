#!/usr/bin/env python3
"""Write cross-source reconciliation and ingest transparency reports."""

from __future__ import annotations

import json

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.audit import audit_completeness  # noqa: E402
from src.integration.source_reconciliation import (  # noqa: E402
    ambiguity_buckets,
    conflict_buckets,
    source_contribution_counts,
    venue_alias_collision_summary,
)
from src.seed import load_seed_compendium  # noqa: E402
from src.tier import resolve_seed_dir  # noqa: E402


def main() -> int:
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp = load_seed_compendium(seed_dir=resolve_seed_dir())
    completeness = audit_completeness(comp)

    ingest_path = ROOT / "output" / "archival" / "build_report.json"
    ingest_stats: dict[str, int] = {}
    skipped: list[str] = []
    sources_used: list[str] = []
    if ingest_path.is_file():
        payload = json.loads(ingest_path.read_text(encoding="utf-8"))
        ingest_stats = payload.get("ingest_stats") or {}
        skipped = payload.get("skipped") or []
        sources_used = payload.get("sources_used") or []

    report = {
        "completeness": completeness.to_dict(),
        "ingest_stats": ingest_stats,
        "skipped_sources": skipped,
        "source_contributions": source_contribution_counts(
            comp, ingest_stats=ingest_stats, sources_used=sources_used
        ),
        "conflict_buckets": conflict_buckets(
            ingest_stats=ingest_stats, skipped_sources=skipped
        ),
        "ambiguity_buckets": ambiguity_buckets(comp),
        "venue_alias_summary": venue_alias_collision_summary(comp),
    }
    path = out_dir / "source_reconciliation.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(path)
    print(
        f"lyric_gaps={completeness.performed_songs_without_lyric_pointer} "
        f"shows_empty={len(completeness.shows_without_performances)} "
        f"ia_dropped_date={ingest_stats.get('recordings_dropped_date', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
