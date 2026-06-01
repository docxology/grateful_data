"""Complete raw-data export of the compendium.

Writes every reconciled entity to ``<out_dir>/<entity>.csv`` plus a single
``compendium_full.json`` containing *all* records (not just counts). The
export is deterministic — sorted iteration, ISO dates — so re-running over the
same seed yields byte-identical files. It computes purely over the bundled
seed; no field is invented (honesty boundary stays load-bearing).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .analysis.geo import load_geo
from .analysis.segues import segue_edges
from .integration.reconcile import Compendium


def _write_csv(path: Path, header: list[str], rows: list[list]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def _intervals_str(person) -> str:
    """Serialise a Person's (start, end, role) intervals as a stable string."""
    return "; ".join(
        f"{start.isoformat()}..{end.isoformat() if end else ''}:{role}"
        for start, end, role in person.intervals
    )


def export_all(
    comp: Compendium, out_dir: Path | str, geo: dict | None = None
) -> dict[str, Path]:
    """Export every entity to CSV + a complete JSON. Returns name -> path."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    geo_map = geo if geo is not None else load_geo()
    written: dict[str, Path] = {}

    written["shows"] = _write_csv(
        out / "shows.csv",
        ["slug", "date", "venue_slug", "tour", "notes"],
        [
            [s.slug, s.date.isoformat(), s.venue_slug, s.tour or "", s.notes]
            for s in comp.shows
        ],
    )
    written["performances"] = _write_csv(
        out / "performances.csv",
        ["show_slug", "song_slug", "set_number", "position", "segue_into", "notes"],
        [
            [
                p.show_slug,
                p.song_slug,
                p.set_number,
                p.position,
                p.segue_into or "",
                p.notes,
            ]
            for p in comp.performances
        ],
    )
    written["songs"] = _write_csv(
        out / "songs.csv",
        [
            "slug",
            "title",
            "composers",
            "lyricists",
            "first_performed",
            "last_performed",
            "aliases",
        ],
        [
            [
                s.slug,
                s.title,
                ";".join(s.composers),
                ";".join(s.lyricists),
                s.first_performed.isoformat() if s.first_performed else "",
                s.last_performed.isoformat() if s.last_performed else "",
                ";".join(s.aliases),
            ]
            for s in comp.songs
        ],
    )
    written["venues"] = _write_csv(
        out / "venues.csv",
        ["slug", "name", "city", "state_or_region", "country"],
        [[v.slug, v.name, v.city, v.state_or_region, v.country] for v in comp.venues],
    )
    written["personnel"] = _write_csv(
        out / "personnel.csv",
        ["slug", "full_name", "intervals"],
        [[p.slug, p.full_name, _intervals_str(p)] for p in comp.people],
    )
    written["recordings"] = _write_csv(
        out / "recordings.csv",
        ["archive_id", "show_slug", "source_type", "url"],
        [[r.archive_id, r.show_slug, r.source_type, r.url] for r in comp.recordings],
    )
    written["releases"] = _write_csv(
        out / "releases.csv",
        ["slug", "title", "release_date", "kind", "track_show_slugs"],
        [
            [
                r.slug,
                r.title,
                r.release_date.isoformat(),
                r.kind,
                ";".join(r.track_show_slugs),
            ]
            for r in comp.releases
        ],
    )
    written["citations"] = _write_csv(
        out / "citations.csv",
        ["key", "title", "url", "kind", "year"],
        [
            [c.key, c.title, c.url, c.kind, c.year if c.year is not None else ""]
            for c in comp.citations
        ],
    )
    written["reviews"] = _write_csv(
        out / "reviews.csv",
        ["show_slug", "author", "sentiment", "summary", "source_url", "kind"],
        [
            [r.show_slug, r.author, r.sentiment, r.summary, r.source_url, r.kind]
            for r in comp.reviews
        ],
    )
    written["lyric_pointers"] = _write_csv(
        out / "lyric_pointers.csv",
        ["song_slug", "lyricist", "source_url", "themes"],
        [
            [lp.song_slug, lp.lyricist, lp.source_url, ";".join(lp.themes)]
            for lp in comp.lyric_pointers
        ],
    )
    written["venue_geo"] = _write_csv(
        out / "venue_geo.csv",
        ["venue_slug", "lat", "lon", "region"],
        [
            [slug, info["lat"], info["lon"], info["region"]]
            for slug, info in sorted(geo_map.items())
        ],
    )
    written["segues"] = _write_csv(
        out / "segues.csv",
        ["src", "dst", "count"],
        [[e.src, e.dst, e.count] for e in segue_edges(comp)],
    )

    written["compendium_full.json"] = _write_full_json(
        comp, out / "compendium_full.json", geo_map
    )
    return written


def _records_from_csv_specs(comp: Compendium, geo_map: dict) -> dict[str, list[dict]]:
    """Full per-entity record lists for the JSON export."""
    return {
        "shows": [
            {
                "slug": s.slug,
                "date": s.date.isoformat(),
                "venue_slug": s.venue_slug,
                "tour": s.tour,
                "notes": s.notes,
            }
            for s in comp.shows
        ],
        "performances": [
            {
                "show_slug": p.show_slug,
                "song_slug": p.song_slug,
                "set_number": p.set_number,
                "position": p.position,
                "segue_into": p.segue_into,
                "notes": p.notes,
            }
            for p in comp.performances
        ],
        "songs": [
            {
                "slug": s.slug,
                "title": s.title,
                "composers": list(s.composers),
                "lyricists": list(s.lyricists),
                "first_performed": s.first_performed.isoformat()
                if s.first_performed
                else None,
                "last_performed": s.last_performed.isoformat()
                if s.last_performed
                else None,
                "aliases": list(s.aliases),
            }
            for s in comp.songs
        ],
        "venues": [
            {
                "slug": v.slug,
                "name": v.name,
                "city": v.city,
                "state_or_region": v.state_or_region,
                "country": v.country,
            }
            for v in comp.venues
        ],
        "personnel": [
            {"slug": p.slug, "full_name": p.full_name, "intervals": _intervals_str(p)}
            for p in comp.people
        ],
        "recordings": [
            {
                "archive_id": r.archive_id,
                "show_slug": r.show_slug,
                "source_type": r.source_type,
                "url": r.url,
            }
            for r in comp.recordings
        ],
        "releases": [
            {
                "slug": r.slug,
                "title": r.title,
                "release_date": r.release_date.isoformat(),
                "kind": r.kind,
                "track_show_slugs": list(r.track_show_slugs),
            }
            for r in comp.releases
        ],
        "citations": [
            {
                "key": c.key,
                "title": c.title,
                "url": c.url,
                "kind": c.kind,
                "year": c.year,
            }
            for c in comp.citations
        ],
        "reviews": [
            {
                "show_slug": r.show_slug,
                "author": r.author,
                "sentiment": r.sentiment,
                "summary": r.summary,
                "source_url": r.source_url,
                "kind": r.kind,
            }
            for r in comp.reviews
        ],
        "lyric_pointers": [
            {
                "song_slug": lp.song_slug,
                "lyricist": lp.lyricist,
                "source_url": lp.source_url,
                "themes": list(lp.themes),
            }
            for lp in comp.lyric_pointers
        ],
        "venue_geo": [
            {
                "venue_slug": slug,
                "lat": info["lat"],
                "lon": info["lon"],
                "region": info["region"],
            }
            for slug, info in sorted(geo_map.items())
        ],
        "segues": [
            {"src": e.src, "dst": e.dst, "count": e.count} for e in segue_edges(comp)
        ],
    }


def _write_full_json(comp: Compendium, path: Path, geo_map: dict) -> Path:
    records = _records_from_csv_specs(comp, geo_map)
    payload = {
        "counts": {k: len(v) for k, v in records.items()},
        "records": records,
    }
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path
