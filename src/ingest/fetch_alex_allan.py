"""Alex Allan / whitegum.com song-index fetch adapter."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import LyricPointer, Song, canonical_song_id
from ..sources.alex_allan import parse as parse_song_record
from ._vendor_fetch import fetch_or_read_cache_with_fallbacks, vendor_path

INDEX_URL = "https://www.whitegum.com/intro.htm"
WHITEGUM_FALLBACK_URLS: tuple[str, ...] = (
    INDEX_URL,
    "https://web.archive.org/web/20040601000000/http://www.whitegum.com/intro.htm",
    "https://web.archive.org/web/20020101000000/http://www.whitegum.com/intro.htm",
)
_SONGFILE_RE = re.compile(r'href="songfile/([A-Z0-9_]+)\.HTM"', re.IGNORECASE)


def _songfile_links(html: str) -> list[str]:
    return _SONGFILE_RE.findall(html)


def _title_from_code(code: str) -> str:
    """Best-effort title from whitegum songfile stem (fallback when page lacks title)."""
    return code.replace("_", " ").title()


def fetch_alex_allan_songs(
    *,
    online: bool = False,
    seed_dir: Path | None = None,
) -> tuple[list[Song], list[LyricPointer]]:
    """Load song metadata from vendor cache + curated seed; enrich from whitegum index when online."""
    songs: dict[str, Song] = {}
    pointers: list[LyricPointer] = []

    if seed_dir:
        songs_path = seed_dir / "songs.json"
        if songs_path.is_file():
            raw = json.loads(songs_path.read_text(encoding="utf-8"))
            for row in raw:
                song = parse_song_record(row)
                songs[song.slug] = song
        lp_path = seed_dir / "lyric_pointers.json"
        if lp_path.is_file():
            for row in json.loads(lp_path.read_text(encoding="utf-8")):
                pointers.append(
                    LyricPointer(
                        song_slug=row["song_slug"],
                        lyricist=row["lyricist"],
                        source_url=row["source_url"],
                        themes=tuple(row.get("themes", ())),
                    )
                )

    cache = vendor_path("whitegum", "intro.htm")
    html: str | None = None
    if cache.is_file():
        cached = cache.read_text(encoding="utf-8", errors="replace")
        if _songfile_links(cached):
            html = cached
    if html is None and online:
        try:
            html, _ = fetch_or_read_cache_with_fallbacks(
                source="whitegum",
                filename="intro.htm",
                urls=WHITEGUM_FALLBACK_URLS,
                online=True,
                min_bytes=400,
            )
        except OSError:
            return list(songs.values()), pointers
    if html is None:
        return list(songs.values()), pointers
    if not _songfile_links(html):
        return list(songs.values()), pointers
    for code in _songfile_links(html):
        title = _title_from_code(code)
        slug = canonical_song_id(title)
        url = f"https://www.whitegum.com/songfile/{code}.HTM"
        if slug not in songs:
            songs[slug] = Song(slug=slug, title=title)
        if not any(lp.source_url == url for lp in pointers):
            pointers.append(
                LyricPointer(
                    song_slug=slug,
                    lyricist="",
                    source_url=url,
                    themes=(),
                )
            )

    return list(songs.values()), pointers
