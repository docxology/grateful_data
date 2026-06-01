#!/usr/bin/env python3
"""Generate a peer-review evidence dossier."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.reporting.peer_review import write_peer_review_dossier  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    compendium = load_seed_compendium()
    json_path, markdown_path = write_peer_review_dossier(
        compendium,
        ROOT / "output" / "reports",
        reports_dir=ROOT / "output" / "reports",
        figures_dir=ROOT / "output" / "figures",
    )
    print(f"peer_review_json: {json_path}")
    print(f"peer_review_markdown: {markdown_path}")


if __name__ == "__main__":
    main()
