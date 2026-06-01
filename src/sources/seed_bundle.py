"""Parsers for the bundled seed JSON shape.

The seed fixtures mirror the record shapes documented for external sources but
are stored as normalized JSON under ``data/seed/``. These parsers keep
``seed.load_seed_compendium`` a thin orchestrator and make the bundled load path
testable independently of network fetchers.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from ..models import (
    Citation,
    LyricPointer,
    Performance,
    Review,
    Show,
    Venue,
    canonical_show_id,
    canonical_song_id,
)

_FOOTNOTE_REF = re.compile(r"\[\^\d+\]?")


def _clean_citation_value(value: str) -> str:
    return _FOOTNOTE_REF.sub("", value).strip().rstrip(".,;")


def parse_venue_record(raw: dict[str, Any]) -> Venue:
    return Venue(
        slug=raw["slug"],
        name=raw["name"],
        city=raw["city"],
        state_or_region=raw["state"],
    )


def parse_performance_records(raw_perfs: list[dict[str, Any]]) -> list[Performance]:
    """Parse archival ``performances.json`` rows (authoritative when present)."""
    out: list[Performance] = []
    for raw in raw_perfs:
        out.append(
            Performance(
                show_slug=raw["show_slug"],
                song_slug=raw["song_slug"],
                set_number=int(raw["set_number"]),
                position=int(raw["position"]),
                segue_into=raw.get("segue_into"),
                notes=str(raw.get("notes") or ""),
            )
        )
    return out


def parse_show_records(
    raw_shows: list[dict[str, Any]],
) -> tuple[list[Show], list[Performance]]:
    shows: list[Show] = []
    perfs: list[Performance] = []
    for raw in raw_shows:
        show_date = datetime.strptime(raw["date"], "%Y-%m-%d").date()
        venue_slug = raw["venue_slug"]
        show_index = int(raw.get("show_index", 0) or 0)
        slug = canonical_show_id(show_date, venue_slug, show_index=show_index)
        shows.append(
            Show(
                slug=slug,
                date=show_date,
                venue_slug=venue_slug,
                tour=raw.get("tour"),
            )
        )
        for set_num, titles in raw["setlist"]:
            for pos, title in enumerate(titles, start=1):
                perfs.append(
                    Performance(
                        show_slug=slug,
                        song_slug=canonical_song_id(title),
                        set_number=int(set_num),
                        position=pos,
                    )
                )
    return shows, perfs


def parse_citation_record(raw: dict[str, Any]) -> Citation:
    return Citation(
        key=_clean_citation_value(raw["key"]),
        title=_clean_citation_value(raw["title"]),
        url=_clean_citation_value(raw["url"]),
        kind=raw["kind"],
    )


def parse_lyric_pointer_record(raw: dict[str, Any]) -> LyricPointer:
    return LyricPointer(
        song_slug=raw["song_slug"],
        lyricist=raw["lyricist"],
        source_url=raw["source_url"],
        themes=tuple(raw.get("themes", ())),
    )


def parse_review_record(raw: dict[str, Any]) -> Review:
    return Review(
        show_slug=raw["show_slug"],
        author=raw["author"],
        sentiment=float(raw["sentiment"]),
        summary=raw["summary"],
        source_url=raw["source_url"],
        kind=raw["kind"],
    )
