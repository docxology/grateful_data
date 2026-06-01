#!/usr/bin/env python3
"""Data-completeness audit: prove every show holds full, resolvable data.

Thin orchestrator over :func:`src.audit.audit_completeness`. Writes a
machine-readable report and exits non-zero if any reference is dangling.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.audit import audit_completeness  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> int:
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp = load_seed_compendium()
    report = audit_completeness(comp)

    path = out_dir / "completeness_report.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2)
    print(path)
    print(
        f"complete={report.is_complete} dangling={report.dangling_total} geo={report.geo_coverage_pct:.1f}%"
    )
    print(f"scope: {report.corpus_scope}")
    return 0 if report.is_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
