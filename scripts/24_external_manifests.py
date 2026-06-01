#!/usr/bin/env python3
"""Write pointer-only manifests for external audio and lyric resources."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.external_manifests import write_external_manifests  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    compendium = load_seed_compendium()
    audio_path, lyric_path, summary_path = write_external_manifests(
        compendium, ROOT / "output" / "data" / "external"
    )
    print(f"audio_manifest: {audio_path}")
    print(f"lyric_manifest: {lyric_path}")
    print(f"summary: {summary_path}")
    print(f"pipeline_contract: {summary_path.parent / 'pipeline_contract.json'}")


if __name__ == "__main__":
    main()
