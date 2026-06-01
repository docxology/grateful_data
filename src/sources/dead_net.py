"""Parser for the official ``dead.net`` band-members page.

The official band site lists members with role labels (lead guitar, rhythm
guitar, bass, drums, keyboards, harmonica) and joining/leaving years. We
accept records of the shape::

    {
      "slug": "garcia",
      "full_name": "Jerry Garcia",
      "intervals": [
        {"start": "1965-01-01", "end": "1995-08-09", "role": "lead guitar"},
        {"start": "1965-01-01", "end": "1995-08-09", "role": "vocals"}
      ]
    }
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import Person

CITATION_KEY = "dead_net_official"


def _parse_interval(blob: dict[str, str]) -> tuple:
    start = datetime.strptime(blob["start"], "%Y-%m-%d").date()
    end_raw = blob.get("end")
    end = datetime.strptime(end_raw, "%Y-%m-%d").date() if end_raw else None
    return (start, end, blob["role"])


def parse(record: dict[str, Any]) -> Person:
    """Parse a ``dead.net`` member record into a ``Person``."""
    intervals = tuple(_parse_interval(b) for b in record.get("intervals", []))
    return Person(
        slug=record["slug"],
        full_name=record["full_name"],
        intervals=intervals,
    )
