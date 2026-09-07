#!/usr/bin/env python3
"""Emit manuscript variables and hydrate ``output/manuscript/`` for PDF render.

Thin orchestrator over :mod:`src.reporting.manuscript`.
"""

from __future__ import annotations

from _bootstrap import ensure_project_root

ensure_project_root()

from src.reporting.manuscript import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
