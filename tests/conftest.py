"""Shared pytest fixtures.

Per project policy: no mocks. Fixtures load the real bundled seed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make ``src/`` importable as a top-level package alias.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.seed import load_seed_compendium  # noqa: E402
from src.tier import ARCHIVAL_DIR  # noqa: E402


_SEED_DATA = _PROJECT_ROOT / "data" / "seed"


@pytest.fixture(scope="session")
def compendium():
    """Real, bundled seed compendium — shared across all tests."""
    return load_seed_compendium(_SEED_DATA)


@pytest.fixture(scope="session")
def archival_compendium():
    """Committed archival snapshot when present."""
    if not ARCHIVAL_DIR.is_dir() or not (ARCHIVAL_DIR / "shows.json").exists():
        pytest.skip("data/archival snapshot not present")
    return load_seed_compendium(ARCHIVAL_DIR)
