"""Serialize a reconciled compendium to seed-shaped JSON files."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from ..integration.reconcile import Compendium
from ..validation import assert_valid


def _person_to_json(person) -> dict:
    return {
        "slug": person.slug,
        "full_name": person.full_name,
        "intervals": [
            {
                "start": start.isoformat(),
                "end": end.isoformat() if end else None,
                "role": role,
            }
            for start, end, role in person.intervals
        ],
    }


def _song_to_json(song) -> dict:
    row: dict = {"title": song.title}
    if song.composers:
        row["composers"] = list(song.composers)
    if song.lyricists:
        row["lyricists"] = list(song.lyricists)
    if song.first_performed:
        row["first_performed"] = song.first_performed.isoformat()
    if song.last_performed:
        row["last_performed"] = song.last_performed.isoformat()
    if song.aliases:
        row["aliases"] = list(song.aliases)
    return row


def compendium_to_seed_files(
    comp: Compendium, out_dir: Path, geo_rows: list[dict]
) -> None:
    """Write all seed JSON files under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    title_by_slug = {s.slug: s.title for s in comp.songs}

    perf_by_show: dict[str, list] = defaultdict(list)
    for p in comp.performances:
        perf_by_show[p.show_slug].append(p)

    shows_json: list[dict] = []
    for show in comp.shows:
        set_map: dict[int, list[str]] = defaultdict(list)
        for perf in sorted(
            perf_by_show.get(show.slug, []), key=lambda x: (x.set_number, x.position)
        ):
            title = title_by_slug.get(perf.song_slug, perf.song_slug)
            set_map[perf.set_number].append(title)
        setlist = [[set_num, titles] for set_num, titles in sorted(set_map.items())]
        show_index = 0
        if "#" in show.slug:
            show_index = int(show.slug.rsplit("#", 1)[-1])
        row: dict = {
            "date": show.date.isoformat(),
            "venue_slug": show.venue_slug,
            "setlist": setlist,
        }
        if show_index:
            row["show_index"] = show_index
        if show.tour:
            row["tour"] = show.tour
        shows_json.append(row)

    venues_json = [
        {
            "slug": v.slug,
            "name": v.name,
            "city": v.city,
            "state": v.state_or_region,
        }
        for v in comp.venues
    ]

    songs_json = [_song_to_json(s) for s in comp.songs]
    personnel_json = [_person_to_json(p) for p in comp.people]

    recordings_json = []
    for rec in comp.recordings:
        date_part = rec.show_slug.split("@")[0]
        venue_part = rec.show_slug.split("@")[-1] if "@" in rec.show_slug else ""
        recordings_json.append(
            {
                "identifier": rec.archive_id,
                "date": date_part,
                "venue": venue_part.replace("_", " "),
                "coverage": "",
                "source": rec.source_type,
                "show_slug": rec.show_slug,
            }
        )

    releases_json = [
        {
            "title": r.title,
            "release_date": r.release_date.isoformat(),
            "kind": r.kind,
        }
        for r in comp.releases
    ]

    citations_json = [
        {"key": c.key, "title": c.title, "url": c.url, "kind": c.kind}
        for c in comp.citations
    ]

    lyric_json = [
        {
            "song_slug": lp.song_slug,
            "lyricist": lp.lyricist,
            "source_url": lp.source_url,
            **({"themes": list(lp.themes)} if lp.themes else {}),
        }
        for lp in comp.lyric_pointers
    ]

    reviews_json = [
        {
            "show_slug": r.show_slug,
            "author": r.author,
            "sentiment": r.sentiment,
            "summary": r.summary,
            "source_url": r.source_url,
            "kind": r.kind,
        }
        for r in comp.reviews
    ]

    performances_json = []
    for perf in sorted(
        comp.performances, key=lambda p: (p.show_slug, p.set_number, p.position)
    ):
        perf_row: dict = {
            "show_slug": perf.show_slug,
            "song_slug": perf.song_slug,
            "set_number": perf.set_number,
            "position": perf.position,
        }
        if perf.segue_into:
            perf_row["segue_into"] = perf.segue_into
        if perf.notes:
            perf_row["notes"] = perf.notes
        performances_json.append(perf_row)

    payloads = {
        "shows.json": shows_json,
        "songs.json": songs_json,
        "personnel.json": personnel_json,
        "venues.json": venues_json,
        "performances.json": performances_json,
        "recordings.json": recordings_json,
        "releases.json": releases_json,
        "citations.json": citations_json,
        "lyric_pointers.json": lyric_json,
        "reviews.json": reviews_json,
        "venue_geo.json": geo_rows,
    }

    for name, data in payloads.items():
        path = out_dir / name
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=False)
            fh.write("\n")

    assert_valid(out_dir)
