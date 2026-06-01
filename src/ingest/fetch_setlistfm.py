"""Setlist.fm fetch adapter (optional; requires SETLISTFM_API_KEY)."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from ..sources import setlistfm

GD_MBID = "bd6ad4a"  # Grateful Dead artist id fragment on setlist.fm


def fetch_setlistfm_shows(
    *, max_pages: int = 5, sleep_s: float = 0.55
) -> list[dict[str, Any]]:
    """Paginate Setlist.fm setlists when an API key is configured.

    ``max_pages=0`` paginates until the API reports no further setlists.
    """
    api_key = os.environ.get("SETLISTFM_API_KEY", "").strip()
    if not api_key:
        return []
    out: list[dict[str, Any]] = []
    page = 1
    unlimited = max_pages == 0
    while unlimited or page <= max_pages:
        params = urllib.parse.urlencode({"p": page})
        url = f"https://api.setlist.fm/rest/1.0/artist/{GD_MBID}/setlists?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "x-api-key": api_key,
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        setlists = payload.get("setlist") or []
        if not setlists:
            break
        out.extend(setlists)
        total = int(payload.get("total", 0))
        if page * 20 >= total:
            break
        page += 1
        time.sleep(sleep_s)
    return out


def parse_setlistfm_batch(
    payloads: list[dict[str, Any]],
) -> tuple[list, list, list, list]:
    """Parse Setlist.fm payloads into entity lists for merge."""
    from ..models import Performance, Show, Song, Venue

    shows: list[Show] = []
    venues: list[Venue] = []
    songs: list[Song] = []
    perfs: list[Performance] = []
    for blob in payloads:
        show, venue, perf_tuple, song_tuple = setlistfm.parse(blob)
        shows.append(show)
        venues.append(venue)
        songs.extend(song_tuple)
        perfs.extend(perf_tuple)
    return shows, venues, songs, perfs
