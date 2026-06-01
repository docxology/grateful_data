#!/usr/bin/env python3
"""Deprecated: use ``scripts/z_generate_manuscript_variables.py`` instead.

This script only wrote ``output/reports/manuscript_counts.json`` without
hydrating ``output/manuscript/``. Publication PDFs require
``z_generate_manuscript_variables.py`` (``write_resolved_manuscript_tree``).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import z_generate_manuscript_variables as zgen  # noqa: E402


def main() -> int:
    print(
        "warning: generate_manuscript_counts.py is deprecated; "
        "use scripts/z_generate_manuscript_variables.py",
        file=sys.stderr,
    )
    return zgen.main()


if __name__ == "__main__":
    raise SystemExit(main())
