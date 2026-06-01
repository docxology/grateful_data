"""Lyric-pointer consolidation: curated overlays, catalog propagation, dead.net gap-fill."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from ..integration.aliases import SONG_ALIAS_MAP, canonicalize_alias
from ..models import LyricPointer, Song

DEAD_NET_SONG_BASE = "https://www.dead.net/song"


def dead_net_song_url(song_slug: str) -> str:
    """Build a dead.net song page URL from the compendium song slug."""
    return f"{DEAD_NET_SONG_BASE}/{song_slug.replace('_', '-')}"


def _reverse_alias_map() -> dict[str, str]:
    """Map alias slugs and canonical slugs to canonical theme/lyricist keys."""
    rev: dict[str, str] = {}
    for alias, canonical in SONG_ALIAS_MAP.items():
        rev[alias] = canonical
        rev[canonical] = canonical
    return rev


def _lookup_slug_key(slug: str, table: Mapping[str, object]) -> object | None:
    """Resolve ``slug`` through alias map for overlay tables keyed by canonical slug."""
    canonical = canonicalize_alias(slug)
    if canonical in table:
        return table[canonical]
    rev = _reverse_alias_map()
    key = rev.get(slug, slug)
    return table.get(key)


def _curated_overlay_maps(
    curated_rows: list[dict],
) -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    """Return ``(themes_by_slug, lyricist_by_slug)`` from seed lyric pointer rows."""
    themes_by_slug: dict[str, tuple[str, ...]] = {}
    lyricist_by_slug: dict[str, str] = {}
    for row in curated_rows:
        slug = canonicalize_alias(str(row.get("song_slug", "")).strip())
        if not slug:
            continue
        themes = row.get("themes") or ()
        if isinstance(themes, list) and themes:
            themes_by_slug[slug] = tuple(str(t) for t in themes)
        lyricist = str(row.get("lyricist", "")).strip()
        if lyricist:
            lyricist_by_slug[slug] = lyricist
    return themes_by_slug, lyricist_by_slug


def overlay_curated_lyric_metadata(
    pointers: list[LyricPointer],
    curated_rows: list[dict] | None,
) -> list[LyricPointer]:
    """Apply seed themes and lyricist labels with alias-aware slug resolution."""
    if not curated_rows:
        return pointers
    themes_by_slug, lyricist_by_slug = _curated_overlay_maps(curated_rows)
    if not themes_by_slug and not lyricist_by_slug:
        return pointers
    enriched: list[LyricPointer] = []
    for lp in pointers:
        themes = lp.themes
        if not themes:
            found = _lookup_slug_key(lp.song_slug, themes_by_slug)
            if isinstance(found, tuple):
                themes = found
        lyricist = lp.lyricist
        if not lyricist:
            found = _lookup_slug_key(lp.song_slug, lyricist_by_slug)
            if isinstance(found, str):
                lyricist = found
        if themes != lp.themes or lyricist != lp.lyricist:
            enriched.append(replace(lp, themes=themes, lyricist=lyricist))
        else:
            enriched.append(lp)
    return enriched


def propagate_song_lyricists(
    pointers: list[LyricPointer],
    songs: list[Song],
) -> tuple[list[LyricPointer], int]:
    """Fill empty ``lyricist`` fields from the reconciled song catalog."""
    by_slug = {s.slug: s for s in songs}
    updated = 0
    out: list[LyricPointer] = []
    for lp in pointers:
        if lp.lyricist:
            out.append(lp)
            continue
        song = by_slug.get(lp.song_slug) or by_slug.get(
            canonicalize_alias(lp.song_slug)
        )
        if not song or not song.lyricists:
            out.append(lp)
            continue
        out.append(replace(lp, lyricist="; ".join(song.lyricists)))
        updated += 1
    return out, updated


def fill_dead_net_lyric_gaps(
    performed_song_slugs: set[str],
    pointers: list[LyricPointer],
    songs: list[Song],
    *,
    require_lyricist: bool = False,
) -> tuple[list[LyricPointer], int]:
    """Add dead.net song-page pointers for performed songs missing any lyric URL."""
    covered = {lp.song_slug for lp in pointers}
    by_slug = {s.slug: s for s in songs}
    added = 0
    out = list(pointers)
    for slug in sorted(performed_song_slugs):
        if slug in covered:
            continue
        song = by_slug.get(slug) or by_slug.get(canonicalize_alias(slug))
        if require_lyricist and (not song or not song.lyricists):
            continue
        lyricist = "; ".join(song.lyricists) if song and song.lyricists else ""
        out.append(
            LyricPointer(
                song_slug=slug,
                lyricist=lyricist,
                source_url=dead_net_song_url(slug),
                themes=(),
            ),
        )
        covered.add(slug)
        added += 1
    return out, added


def consolidate_lyric_pointers(
    pointers: list[LyricPointer],
    songs: list[Song],
    *,
    performed_song_slugs: set[str] | None = None,
    curated_rows: list[dict] | None = None,
    fill_dead_net: bool = True,
) -> tuple[list[LyricPointer], dict[str, int]]:
    """Overlay curated metadata, propagate catalog lyricists, and back-fill dead.net."""
    stats: dict[str, int] = {
        "overlayed": 0,
        "lyricists_propagated": 0,
        "dead_net_added": 0,
    }
    merged = overlay_curated_lyric_metadata(pointers, curated_rows)
    if curated_rows:
        stats["overlayed"] = sum(
            1 for a, b in zip(pointers, merged, strict=False) if a != b
        )
    merged, propagated = propagate_song_lyricists(merged, songs)
    stats["lyricists_propagated"] = propagated
    if fill_dead_net:
        perf_slugs = performed_song_slugs or {s.slug for s in songs}
        merged, added = fill_dead_net_lyric_gaps(
            perf_slugs, merged, songs, require_lyricist=False
        )
        stats["dead_net_added"] = added
    stats["total"] = len(merged)
    stats["with_lyricist"] = sum(1 for lp in merged if lp.lyricist)
    stats["with_themes"] = sum(1 for lp in merged if lp.themes)
    return merged, stats
