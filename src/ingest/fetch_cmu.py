"""CMU / Mark Leone setlist archive fetch adapter."""

from __future__ import annotations

import re
from html import unescape

from ..sources import cmu_setlists
from ._vendor_fetch import fetch_or_read_cache_with_fallbacks

CMU_URL = "http://www.cs.cmu.edu/~mleone/gs.html"
CMU_FALLBACK_URLS: tuple[str, ...] = (
    CMU_URL,
    "https://web.archive.org/web/20150107095256id_/http://www.cs.cmu.edu/~mleone/gs.html",
    "https://web.archive.org/web/20150107095256/http://www.cs.cmu.edu/~mleone/gs.html",
    "https://web.archive.org/web/20240101000000/http://www.cs.cmu.edu/~mleone/gs.html",
    "https://web.archive.org/web/20220101000000/http://www.cs.cmu.edu/~mleone/gs.html",
)
_BLOCK_SPLIT = re.compile(r"(?=^\d{4}-\d{2}-\d{2}\s)", re.MULTILINE)
_HTML_PRE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")


def split_cmu_blocks(text: str) -> list[str]:
    """Split raw CMU archive text into per-show blocks."""
    chunks = [c.strip() for c in _BLOCK_SPLIT.split(text) if c.strip()]
    return [c for c in chunks if re.match(r"^\d{4}-\d{2}-\d{2}\s", c)]


def normalize_cmu_archive_text(text: str) -> str:
    """Strip Wayback/HTML wrappers when the archive is not plain text."""
    if "<html" not in text.lower():
        return text
    pre_blocks = _HTML_PRE.findall(text)
    if pre_blocks:
        return "\n".join(unescape(_TAG.sub("", block)) for block in pre_blocks)
    stripped = unescape(_TAG.sub(" ", text))
    return re.sub(r"\s+", " ", stripped)


def fetch_cmu_shows(*, online: bool = False) -> tuple[list, list, list, list, str]:
    """Fetch and parse CMU setlist blocks into entity lists.

    Returns ``(shows, venues, songs, performances, source_label)``.
    """
    text, source_label = fetch_or_read_cache_with_fallbacks(
        source="cmu",
        filename="gs.html",
        urls=CMU_FALLBACK_URLS,
        online=online,
        min_bytes=5_000,
    )
    text = normalize_cmu_archive_text(text)
    blocks = split_cmu_blocks(text)
    if not blocks:
        raise OSError(
            "cmu_leone_setlists: no parseable show blocks "
            "(Wayback snapshots currently return wrapper HTML only)"
        )
    shows: list = []
    venues: list = []
    songs: list = []
    perfs: list = []
    for block in blocks:
        try:
            show, venue, perf_tuple, song_tuple = cmu_setlists.parse(block)
        except ValueError:
            continue
        shows.append(show)
        venues.append(venue)
        songs.extend(song_tuple)
        perfs.extend(perf_tuple)
    return shows, venues, songs, perfs, source_label
