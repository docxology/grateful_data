"""CMU / Mark Leone dead-lyrics index fetch adapter (pointer metadata only)."""

from __future__ import annotations

import re

from ..models import LyricPointer, canonical_song_id
from ._vendor_fetch import fetch_or_read_cache_with_fallbacks

CMU_LYRICS_URL = "http://www.cs.cmu.edu/~mleone/dead-lyrics.html"
CMU_LYRICS_FALLBACK_URLS: tuple[str, ...] = (
    CMU_LYRICS_URL,
    "https://web.archive.org/web/20200101000000/http://www.cs.cmu.edu/~mleone/dead-lyrics.html",
    "https://web.archive.org/web/20150101000000/http://www.cs.cmu.edu/~mleone/dead-lyrics.html",
    "https://web.archive.org/web/20100101000000/http://www.cs.cmu.edu/~mleone/dead-lyrics.html",
)

_LYRIC_HREF = re.compile(
    r'href="(?P<path>gdead/dead-lyrics/[^"]+\.txt)"', re.IGNORECASE
)
_TITLE_FROM_PATH = re.compile(r"/([^/]+)\.txt$")


def _title_from_lyric_path(path: str) -> str:
    match = _TITLE_FROM_PATH.search(path.replace("\\", "/"))
    if not match:
        return ""
    stem = match.group(1)
    return stem.replace("_", " ").strip()


def _resolve_source_url(path: str, base_url: str) -> str:
    if base_url.startswith("cache:") or "web.archive.org" not in base_url:
        return f"https://web.archive.org/web/20150101000000/http://www.cs.cmu.edu/~mleone/{path}"
    if "web.archive.org" in base_url:
        prefix = base_url.split("/http", 1)[0]
        return f"{prefix}/http://www.cs.cmu.edu/~mleone/{path}"
    return f"https://www.cs.cmu.edu/~mleone/{path}"


def parse_cmu_lyrics_index(
    html: str, *, base_url: str = CMU_LYRICS_URL
) -> list[LyricPointer]:
    """Parse CMU lyric index HTML into pointer rows (no lyric text loaded)."""
    pointers: list[LyricPointer] = []
    seen: set[tuple[str, str]] = set()
    for match in _LYRIC_HREF.finditer(html):
        path = match.group("path")
        title = _title_from_lyric_path(path)
        if not title:
            continue
        slug = canonical_song_id(title)
        source_url = _resolve_source_url(path, base_url)
        key = (slug, source_url)
        if key in seen:
            continue
        seen.add(key)
        pointers.append(
            LyricPointer(song_slug=slug, lyricist="", source_url=source_url, themes=())
        )
    return pointers


def fetch_cmu_lyric_pointers(*, online: bool) -> tuple[list[LyricPointer], str]:
    """Fetch CMU dead-lyrics index and return pointers plus source label."""
    text, source_label = fetch_or_read_cache_with_fallbacks(
        source="cmu",
        filename="dead-lyrics.html",
        urls=CMU_LYRICS_FALLBACK_URLS,
        online=online,
        min_bytes=5_000,
    )
    return parse_cmu_lyrics_index(text, base_url=source_label), source_label
