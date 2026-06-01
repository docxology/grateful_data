"""Parser for Internet Archive Live Music Archive recording metadata.

The Internet Archive's Live Music Archive (``archive.org/details/GratefulDead``)
serves recording metadata as a JSON document with the shape::

    {
      "metadata": {
        "identifier": "gd1977-05-08.sbd.miller.110987.flac16",
        "date": "1977-05-08",
        "venue": "Barton Hall, Cornell University",
        "coverage": "Ithaca, NY",
        "source": "SBD",
        "creator": "Grateful Dead"
      }
    }

We normalize this into a ``Recording`` with the show slug computed from the
date and venue (the same slug rule used elsewhere — that's the join key for
``integration.reconcile``).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import Recording, canonical_show_id

CITATION_KEY = "internet_archive_lma"

_VALID_SOURCE_MAP = {
    "SBD": "SBD",
    "AUD": "AUD",
    "MTX": "MTX",
    "MATRIX": "MTX",
    "FM": "FM",
}


def _venue_slug(name: str, coverage: str) -> str:
    city = coverage.split(",")[0].strip()
    raw = f"{name}_{city}".lower()
    out: list[str] = []
    for ch in raw:
        out.append(ch if ch.isalnum() else "_")
    return "_".join(filter(None, "".join(out).split("_")))


def _parse_ia_date(raw: str) -> date:
    """Internet Archive dates may be ``YYYY-MM-DD`` or ISO datetime strings."""
    return datetime.strptime(raw[:10], "%Y-%m-%d").date()


def date_from_archive_id(archive_id: str) -> str | None:
    """Extract ``YYYY-MM-DD`` from a Grateful Dead IA identifier.

    Handles both four-digit years (``gd1977-05-08…``) and two-digit years
    (``gd77-05-08…``) used by older Live Music Archive uploads.
    Returns ``None`` when the encoded date is not a valid calendar date.
    """
    from datetime import datetime

    if not archive_id.lower().startswith("gd") or len(archive_id) < 10:
        return None
    rest = archive_id[2:]
    encoded: str | None = None
    if len(rest) >= 10 and rest[4] == "-" and rest[:4].isdigit():
        encoded = rest[:10]
    elif len(rest) >= 8 and rest[2] == "-" and rest[:2].isdigit():
        yy = int(rest[:2])
        year = 1900 + yy if yy >= 65 else 2000 + yy
        encoded = f"{year}{rest[2:8]}"
    if encoded is None:
        return None
    try:
        datetime.strptime(encoded, "%Y-%m-%d")
    except ValueError:
        return None
    return encoded


def parse(payload: dict[str, Any]) -> Recording:
    """Parse an Internet Archive metadata blob into a ``Recording``."""
    meta = payload["metadata"]
    if meta.get("show_slug"):
        show_slug = str(meta["show_slug"])
        show_date = _parse_ia_date(meta["date"])
    else:
        show_date = _parse_ia_date(meta["date"])
        venue = meta.get("venue", "")
        coverage = meta.get("coverage", "")
        slug = _venue_slug(venue, coverage)
        show_slug = canonical_show_id(show_date, slug)
    src = meta.get("source", "UNKNOWN").upper()
    source_type = _VALID_SOURCE_MAP.get(src, "UNKNOWN")
    return Recording(
        archive_id=meta["identifier"],
        show_slug=show_slug,
        source_type=source_type,
        url=f"https://archive.org/details/{meta['identifier']}",
    )
