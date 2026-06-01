"""Archival corpus ingestion: fetch, merge, and write seed-shaped JSON."""

from .build import BuildReport, build_archival_compendium, write_archival_snapshot

__all__ = ["BuildReport", "build_archival_compendium", "write_archival_snapshot"]
