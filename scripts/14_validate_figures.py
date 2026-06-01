#!/usr/bin/env python3
"""Validate every rendered figure; fail loudly on a missing/degenerate one."""

from __future__ import annotations

import json

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.viz.figures import EXPECTED_FILENAMES  # noqa: E402
from src.viz.validate import validate_figures  # noqa: E402


def main() -> int:
    figures_dir = ROOT / "output" / "figures"
    out_dir = ROOT / "output" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = validate_figures(figures_dir, expected=EXPECTED_FILENAMES)
    path = out_dir / "figure_validation.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2)
    print(path)
    print(
        f"figures ok={report.n_ok}/{len(report.results)} missing={len(report.missing)} all_ok={report.all_ok}"
    )
    for r in report.results:
        if not r.ok:
            print(f"  FAIL {r.path}: {'; '.join(r.reasons)}")
    for m in report.missing:
        print(f"  MISSING {m}")
    return 0 if report.all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
