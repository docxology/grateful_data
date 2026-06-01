"""Parser for Wikipedia infobox-derived discography and member records.

We accept already-extracted Wikipedia records (the ``wikitext`` parsing layer
lives outside this module — typically a fetcher in ``scripts/`` invokes the
Wikipedia API and emits a normalized JSON). Two record types are supported:

* ``release`` — for ``Grateful Dead discography``
* ``person`` — for biographical entries

This module is intentionally about the SHAPE we expect, not about HTML
scraping. Web parsing is upstream; semantics is here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import Person, Release

CITATION_KEY = "wikipedia_gd"


def _slugify(title: str) -> str:
    out = []
    for ch in title.lower():
        out.append(ch if ch.isalnum() else "_")
    return "_".join(filter(None, "".join(out).split("_")))


def parse_release(record: dict[str, Any]) -> Release:
    """Parse a Wikipedia release record."""
    release_date = datetime.strptime(record["release_date"], "%Y-%m-%d").date()
    return Release(
        slug=_slugify(record["title"]),
        title=record["title"],
        release_date=release_date,
        kind=record.get("kind", "studio"),
        track_show_slugs=tuple(record.get("track_show_slugs", ())),
    )


def parse_person(record: dict[str, Any]) -> Person:
    """Parse a Wikipedia member record."""
    intervals = tuple(
        (
            datetime.strptime(b["start"], "%Y-%m-%d").date(),
            datetime.strptime(b["end"], "%Y-%m-%d").date() if b.get("end") else None,
            b["role"],
        )
        for b in record.get("intervals", [])
    )
    return Person(
        slug=record["slug"],
        full_name=record["full_name"],
        intervals=intervals,
    )
