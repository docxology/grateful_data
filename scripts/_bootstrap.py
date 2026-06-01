"""Shared script bootstrap: project root on sys.path and headless matplotlib."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_project_root(*, matplotlib_backend: bool = False) -> Path:
    """Insert project root on ``sys.path``; optionally configure Agg backend."""
    root = project_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if matplotlib_backend:
        os.environ.setdefault("MPLBACKEND", "Agg")
        import matplotlib

        matplotlib.use("Agg")
    return root
