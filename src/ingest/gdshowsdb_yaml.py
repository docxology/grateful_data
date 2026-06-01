"""Load gdshowsdb year YAML files into the dict-of-tables shape for :mod:`src.sources.gdshowsdb`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..models import canonical_show_id, canonical_song_id, normalize_slug
from ._yaml_utils import get

SKIP_FILES = frozenset({"shows-debug.yaml", "song_refs.yaml"})


def _parse_date_key(date_key: str | int) -> tuple[str, int]:
    """Parse gdshowsdb keys like ``1966/03/03`` or ``1966/03/03/1``."""
    parts = str(date_key).strip().split("/")
    if len(parts) < 3:
        raise ValueError(f"invalid gdshowsdb date key: {date_key!r}")
    year, month, day = parts[0], parts[1], parts[2]
    show_index = int(parts[3]) if len(parts) > 3 else 0
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}", show_index


def _venue_slug(name: str, city: str) -> str:
    return normalize_slug(f"{name}_{city}")


def load_gdshowsdb_vendor(vendor_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Parse all year YAML files under ``vendor_dir/data/gdshowsdb/``."""
    yaml_root = vendor_dir / "data" / "gdshowsdb"
    if not yaml_root.is_dir():
        yaml_root = vendor_dir
    if not yaml_root.is_dir():
        raise FileNotFoundError(f"gdshowsdb YAML root not found under {vendor_dir}")

    venues: dict[str, dict[str, Any]] = {}
    songs: dict[str, dict[str, Any]] = {}
    shows: list[dict[str, Any]] = []
    performances: list[dict[str, Any]] = []

    for path in sorted(yaml_root.glob("*.yaml")):
        if path.name in SKIP_FILES:
            continue
        year_data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(year_data, dict):
            continue
        for date_key, show_blob in year_data.items():
            if not isinstance(show_blob, dict):
                continue
            date_str, show_index = _parse_date_key(date_key)
            venue_name = str(get(show_blob, "venue", ""))
            city = str(get(show_blob, "city", ""))
            state = str(get(show_blob, "state", ""))
            country = str(get(show_blob, "country", "USA"))
            if country == "US":
                country = "USA"
            vslug = _venue_slug(venue_name, city)
            venues[vslug] = {
                "venue_slug": vslug,
                "name": venue_name,
                "city": city,
                "state": state,
                "country": country,
            }
            show_slug = canonical_show_id(
                __import__("datetime").datetime.strptime(date_str, "%Y-%m-%d").date(),
                vslug,
                show_index=show_index,
            )
            shows.append(
                {
                    "show_slug": show_slug,
                    "date": date_str,
                    "venue_slug": vslug,
                    "show_index": show_index,
                    "tour": None,
                }
            )
            set_blobs = get(show_blob, "sets") or []
            for set_idx, set_blob in enumerate(set_blobs, start=1):
                if not isinstance(set_blob, dict):
                    continue
                song_blobs = get(set_blob, "songs") or []
                for pos, song_blob in enumerate(song_blobs, start=1):
                    if not isinstance(song_blob, dict):
                        continue
                    title = str(get(song_blob, "name", "")).strip()
                    if not title:
                        continue
                    sslug = canonical_song_id(title)
                    songs[sslug] = {
                        "song_slug": sslug,
                        "title": title,
                        "composers": [],
                        "lyricists": [],
                    }
                    segued = bool(get(song_blob, "segued", False))
                    segue_into = None
                    if segued and pos < len(song_blobs):
                        nxt = song_blobs[pos]
                        if isinstance(nxt, dict):
                            nxt_title = str(get(nxt, "name", "")).strip()
                            if nxt_title:
                                segue_into = canonical_song_id(nxt_title)
                    perf_row: dict[str, Any] = {
                        "show_slug": show_slug,
                        "song_slug": sslug,
                        "set_number": set_idx,
                        "position": pos,
                    }
                    if segue_into:
                        perf_row["segue_into"] = segue_into
                    performances.append(perf_row)

    return {
        "venues": list(venues.values()),
        "songs": list(songs.values()),
        "shows": shows,
        "performances": performances,
    }
