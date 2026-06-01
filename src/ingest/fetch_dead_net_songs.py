"""dead.net public song-page pointer harvest (HTML scrape; no JSON:API)."""

from __future__ import annotations

import re

from ..models import LyricPointer, canonical_song_id
from .lyric_pointer_enrich import dead_net_song_url
from ._vendor_fetch import fetch_or_read_cache_with_fallbacks

SONGS_URL = "https://www.dead.net/songs"
SONG_HREF = re.compile(r'href="(/song/([a-z0-9\-]+))"', re.IGNORECASE)
TITLE_NEAR = re.compile(
    r'href="/song/[^"]+"[^>]*>\s*([^<]{2,80}?)\s*</a>',
    re.IGNORECASE,
)


def parse_dead_net_song_links(html: str) -> list[LyricPointer]:
    """Extract song-page pointers from dead.net HTML."""
    pointers: list[LyricPointer] = []
    seen: set[str] = set()
    for match in SONG_HREF.finditer(html):
        path = match.group(1)
        hyphen_slug = match.group(2)
        song_slug = canonical_song_id(hyphen_slug.replace("-", " "))
        if song_slug in seen:
            continue
        seen.add(song_slug)
        pointers.append(
            LyricPointer(
                song_slug=song_slug,
                lyricist="",
                source_url=f"https://www.dead.net{path}",
                themes=(),
            ),
        )
    if not pointers:
        for title_match in TITLE_NEAR.finditer(html):
            title = title_match.group(1).strip()
            if not title or title.lower() in {"songs", "the grateful dead"}:
                continue
            song_slug = canonical_song_id(title)
            if song_slug in seen:
                continue
            seen.add(song_slug)
            pointers.append(
                LyricPointer(
                    song_slug=song_slug,
                    lyricist="",
                    source_url=dead_net_song_url(song_slug),
                    themes=(),
                ),
            )
    return pointers


def fetch_dead_net_song_pointers(*, online: bool) -> tuple[list[LyricPointer], str]:
    """Fetch dead.net /songs and return lyric pointers (metadata URLs only)."""
    text, source_label = fetch_or_read_cache_with_fallbacks(
        source="dead_net",
        filename="songs.html",
        urls=(SONGS_URL,),
        online=online,
        min_bytes=500,
    )
    return parse_dead_net_song_links(text), source_label
