"""Internet Archive Live Music Archive fetcher (Grateful Dead collection)."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from ..models import Recording
from ..sources.internet_archive import parse as parse_recording

COLLECTION_QUERY = "collection:GratefulDead AND mediatype:etree"
SEARCH_URL = "https://archive.org/advancedsearch.php"


def fetch_lma_recordings(
    *, max_rows: int = 500, page_size: int = 100
) -> tuple[Recording, ...]:
    """Fetch recording metadata pages from Internet Archive (polite pagination).

    ``max_rows=0`` means no cap (fetch until pagination ends).
    """
    recordings: list[Recording] = []
    page = 1
    unlimited = max_rows == 0
    while unlimited or len(recordings) < max_rows:
        remaining = (
            page_size if unlimited else min(page_size, max_rows - len(recordings))
        )
        params = {
            "q": COLLECTION_QUERY,
            "fl[]": ["identifier", "date", "venue", "coverage", "source"],
            "rows": str(remaining),
            "page": str(page),
            "output": "json",
        }
        url = SEARCH_URL + "?" + urllib.parse.urlencode(params, doseq=True)
        with urllib.request.urlopen(url, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        docs = payload.get("response", {}).get("docs", [])
        if not docs:
            break
        for doc in docs:
            if not doc.get("identifier") or not doc.get("date"):
                continue
            try:
                rec = parse_recording({"metadata": doc})
                recordings.append(rec)
            except (KeyError, ValueError, TypeError):
                continue
        if len(docs) < page_size:
            break
        page += 1
    # Dedupe by archive_id
    seen: set[str] = set()
    unique: list[Recording] = []
    for r in recordings:
        if r.archive_id not in seen:
            seen.add(r.archive_id)
            unique.append(r)
    return tuple(unique)


def fetch_lma_payloads(*, max_rows: int = 500) -> list[dict[str, Any]]:
    """Return raw IA metadata dicts suitable for ``recordings.json`` seed rows."""
    out: list[dict[str, Any]] = []
    for rec in fetch_lma_recordings(max_rows=max_rows):
        out.append(
            {
                "identifier": rec.archive_id,
                "date": rec.show_slug.split("@")[0],
                "venue": rec.show_slug.split("@", 1)[-1].replace("_", " "),
                "coverage": "",
                "source": rec.source_type,
            }
        )
    return out
